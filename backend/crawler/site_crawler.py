"""
crawler/site_crawler.py — Multi-page SSRF-safe Merchant Crawler.
Crawls up to 5 key merchant website pages, extracts metadata, product visuals,
brand logos, certificates, and header banners with strict security controls.

Security & Courtesy:
  - Fetches and respects robots.txt for each domain before crawling.
  - Enforces a minimum 1-second delay between requests to the same domain.
"""

from __future__ import annotations

import html
import json
import logging
import re
import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any, Tuple, Set

import requests
from bs4 import BeautifulSoup

from crawler.ssrf_validator import validate_url_security, is_ip_blocked

logger = logging.getLogger(__name__)


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

_PAGE_TIMEOUT = 8  # seconds per page
_MAX_PAGES = 5      # Maximum pages crawled per site
_MAX_REDIRECTS = 3  # Maximum allowed redirects
_MIN_REQUEST_DELAY_S = 1.0  # Minimum seconds between requests to the same domain

# Module-level caches
_ROBOTS_CACHE: Dict[str, urllib.robotparser.RobotFileParser] = {}
_DOMAIN_LAST_REQUEST: Dict[str, float] = {}


class SafeRedirectSession(requests.Session):
    """Requests session enforcing SSRF validation across all redirect hops."""
    def __init__(self, max_redirects: int = _MAX_REDIRECTS):
        super().__init__()
        self.max_redirect_count = max_redirects
        self.last_redirect_chain: List[Dict[str, Any]] = []

    def resolve_redirects(self, resp, req, stream=False, timeout=None, verify=True, cert=None, proxies=None, yield_requests=False, **adapter_kwargs):
        self.last_redirect_chain = [{"url": resp.url, "status_code": getattr(resp, "status_code", 302)}]
        redirect_count = 0
        for redirect_req in super().resolve_redirects(resp, req, stream=stream, timeout=timeout, verify=verify, cert=cert, proxies=proxies, yield_requests=True, **adapter_kwargs):
            redirect_count += 1
            self.last_redirect_chain.append({"url": redirect_req.url, "status_code": None})
            
            if redirect_count > self.max_redirect_count:
                chain_str = " -> ".join([f"{hop['url']} (status: {hop.get('status_code', 'redirect')})" for hop in self.last_redirect_chain])
                logger.warning("[crawler] Redirect limit exceeded (%d hops): %s", redirect_count, chain_str)
                print(f"[CRAWLER_REDIRECT_LIMIT] Redirect limit exceeded ({redirect_count} hops). Redirect chain: {chain_str}")
                raise requests.exceptions.TooManyRedirects(
                    f"Exceeded maximum allowed redirects ({self.max_redirect_count}). Chain: {chain_str}"
                )
            
            is_valid, ip_addr, err_msg = validate_url_security(redirect_req.url)
            if not is_valid:
                raise requests.exceptions.RequestException(f"SSRF validation blocked redirect to '{redirect_req.url}': {err_msg}")
            
            if yield_requests:
                yield redirect_req
            else:
                resp = self.send(redirect_req, stream=stream, timeout=timeout, verify=verify, cert=cert, proxies=proxies, **adapter_kwargs)
                if self.last_redirect_chain and self.last_redirect_chain[-1]["url"] == redirect_req.url:
                    self.last_redirect_chain[-1]["status_code"] = getattr(resp, "status_code", None)
                yield resp



def _get_robots_parser(domain: str, scheme: str = "https") -> urllib.robotparser.RobotFileParser:
    """
    Fetches and caches robots.txt for `domain`. Returns a RobotFileParser.
    On any fetch failure, returns a permissive (allow-all) parser.
    """
    if domain in _ROBOTS_CACHE:
        return _ROBOTS_CACHE[domain]

    rp = urllib.robotparser.RobotFileParser()
    robots_url = f"{scheme}://{domain}/robots.txt"
    try:
        rp.set_url(robots_url)
        rp.read()  # stdlib does the HTTP fetch
        logger.info("[robots.txt] Fetched and parsed: %s", robots_url)
    except Exception as exc:
        logger.warning("[robots.txt] Could not fetch %s (%s) — treating as allow-all.", robots_url, exc)
        # Permissive fallback: allow everything
        rp = urllib.robotparser.RobotFileParser()
        rp.allow_all = True  # type: ignore[attr-defined]

    _ROBOTS_CACHE[domain] = rp
    return rp


def _is_robots_allowed(url: str, user_agent: str = "*") -> bool:
    """
    Returns True if the given URL is allowed by the domain's robots.txt.
    Falls back to True (allow) on any error.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        scheme = parsed.scheme or "https"
        rp = _get_robots_parser(domain, scheme)
        allowed = rp.can_fetch(user_agent, url)
        if not allowed:
            logger.info("[robots.txt] BLOCKED by robots.txt — skipping: %s", url)
        return allowed
    except Exception:
        return True  # Allow on error


def _enforce_rate_limit(domain: str) -> None:
    """
    Sleeps if the last request to `domain` was less than _MIN_REQUEST_DELAY_S seconds ago.
    Updates the last-request timestamp after sleeping.
    """
    last = _DOMAIN_LAST_REQUEST.get(domain, 0.0)
    elapsed = time.time() - last
    if elapsed < _MIN_REQUEST_DELAY_S:
        sleep_for = _MIN_REQUEST_DELAY_S - elapsed
        logger.debug("[rate-limit] Sleeping %.2fs before next request to %s", sleep_for, domain)
        time.sleep(sleep_for)
    _DOMAIN_LAST_REQUEST[domain] = time.time()


def _classify_page_content(
    soup: Optional[BeautifulSoup],
    full_text: str,
    products: List[Dict[str, Any]],
    image_objects: List[Dict[str, Any]],
    domain: str,
) -> Dict[str, Any]:
    """
    Classifies the crawled merchant website content to determine if it is an
    active e-commerce storefront vs a corporate / fintech / SaaS / informational site.
    """
    if not full_text and not products:
        return {
            "site_category": "UNKNOWN",
            "is_ecommerce": False,
            "confidence": 0.0,
            "summary": f"Insufficient content extracted from {domain}",
            "indicators": [],
        }

    lowered_text = full_text.lower()
    indicators = []

    # E-commerce signals
    has_schema_products = len(products) > 0
    ecommerce_keywords = [
        "add to cart", "buy now", "shopping cart", "checkout", "in stock",
        "out of stock", "shipping & returns", "product details", "sku:",
        "view cart", "price:", "mrp:", "free delivery", "order now", "cart ("
    ]
    ecommerce_keyword_matches = [kw for kw in ecommerce_keywords if kw in lowered_text]

    # Fintech / Payment / Developer signals
    fintech_keywords = [
        "payment gateway", "fintech", "payouts", "banking", "developer documentation",
        "api reference", "api keys", "webhooks", "sdks", "pos machine",
        "payment links", "upi payments", "subscriptions billing", "money transfer",
        "neobanking", "merchant payments", "accept payments"
    ]
    fintech_matches = [kw for kw in fintech_keywords if kw in lowered_text]

    # SaaS / Software signals
    saas_keywords = [
        "saas", "software as a service", "book a demo", "schedule a demo",
        "start free trial", "cloud platform", "integrations", "enterprise security"
    ]
    saas_matches = [kw for kw in saas_keywords if kw in lowered_text]

    # Institutional / Education signals
    institution_keywords = [
        "college", "university", "institute", "faculty", "admissions",
        "syllabus", "curriculum", "academics", "campus", "department"
    ]
    institution_matches = [kw for kw in institution_keywords if kw in lowered_text]

    if has_schema_products or len(ecommerce_keyword_matches) >= 2:
        category = "ECOMMERCE"
        is_ecommerce = True
        summary = f"E-commerce product catalog with {len(products)} detected product items" if products else "E-commerce storefront with active shopping cart/catalog elements"
        indicators = [f"Product markup: {len(products)} items"] + [f"Keyword: '{kw}'" for kw in ecommerce_keyword_matches[:3]]
    elif len(fintech_matches) >= 2 or any(k in domain.lower() for k in ["razorpay", "stripe", "paytm", "phonepe", "cashfree"]):
        category = "FINTECH_PAYMENTS"
        is_ecommerce = False
        summary = "Financial technology & payments platform (non-retail catalog)"
        indicators = [f"Fintech keyword: '{kw}'" for kw in fintech_matches[:3]]
    elif len(saas_matches) >= 2:
        category = "SAAS_SOFTWARE"
        is_ecommerce = False
        summary = "SaaS / Software technology platform (non-retail catalog)"
        indicators = [f"SaaS keyword: '{kw}'" for kw in saas_matches[:3]]
    elif len(institution_matches) >= 2 or any(d in domain.lower() for d in [".ac.in", ".edu", ".org.in"]):
        category = "INFORMATIONAL_INSTITUTION"
        is_ecommerce = False
        summary = "Educational / institutional website (non-retail catalog)"
        indicators = [f"Institutional keyword: '{kw}'" for kw in institution_matches[:3]]
    else:
        category = "GENERAL_WEBSITE"
        is_ecommerce = False
        summary = "General informational / corporate website (no retail product catalog detected)"

    return {
        "site_category": category,
        "is_ecommerce": is_ecommerce,
        "summary": summary,
        "indicators": indicators,
    }


def _find_allowed_candidate_paths(domain: str, scheme: str = "https") -> List[str]:
    """
    Checks common storefront/merchant navigation paths against robots.txt to discover
    permitted alternative landing URLs if the root path '/' is disallowed.
    """
    rp = _get_robots_parser(domain, scheme)
    candidate_subpaths = [
        "/about-us", "/about", "/products", "/shop", "/catalog",
        "/store", "/contact-us", "/contact", "/terms", "/privacy",
        "/collections", "/categories"
    ]
    allowed_urls = []
    for sub in candidate_subpaths:
        candidate_url = f"{scheme}://{domain}{sub}"
        try:
            if rp.can_fetch("*", candidate_url):
                allowed_urls.append(candidate_url)
        except Exception:
            continue
    return allowed_urls


def crawl_merchant(url: str, max_pages: int = _MAX_PAGES) -> Dict[str, Any]:
    """
    Crawls up to `max_pages` of a merchant website starting from `url` in an SSRF-safe manner.
    Discovers key navigation pages (Home, About, Products, Contact, Terms/Policy).
    Explicitly tracks and differentiates failure modes (DNS, timeout, connection refused, 4xx/5xx, robots.txt).
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    is_valid, ip_addr, err_msg = validate_url_security(url)
    if not is_valid:
        error_type = (
            "DNS_RESOLUTION_FAILED"
            if ("DNS resolution failed" in (err_msg or "") or "Could not resolve DNS" in (err_msg or ""))
            else "SSRF_BLOCKED"
            if ("Security validation" in (err_msg or "") or "restricted" in (err_msg or "") or "blocked" in (err_msg or ""))
            else "UNREACHABLE"
        )
        return {
            "url": url,
            "domain": _extract_domain(url),
            "merchant_name": _domain_to_name(_extract_domain(url)),
            "title": "",
            "description": "",
            "raw_text": "",
            "image_objects": [],
            "image_urls": [],
            "products": [],
            "logo_url": None,
            "certificate_urls": [],
            "banner_urls": [],
            "has_contact": False,
            "has_policy": False,
            "has_pricing": False,
            "has_about": False,
            "social_links": [],
            "pages_crawled": [],
            "crawl_status": error_type,
            "crawl_successful": False,
            "error": err_msg or "Failed security or DNS validation.",
            "error_type": error_type,
            "page_classification": {
                "site_category": "UNREACHABLE_SITE",
                "is_ecommerce": False,
                "confidence": 0.0,
                "summary": f"Unreachable domain ({_extract_domain(url)}) — DNS or validation failure",
                "indicators": [],
            },
            "blocked": True,
        }

    domain = _extract_domain(url)
    parsed_u = urlparse(url)
    scheme = parsed_u.scheme or "https"

    all_image_objects: List[Dict[str, Any]] = []
    seen_image_urls: Set[str] = set()
    pages_crawled: List[str] = []
    combined_text: List[str] = []
    products: List[Dict[str, Any]] = []
    social_links: Set[str] = set()
    logo_url: Optional[str] = None
    certificate_urls: List[str] = []
    banner_urls: List[str] = []
    main_title = ""
    main_description = ""
    merchant_name = _domain_to_name(domain)
    root_error: Optional[str] = None
    root_error_type: Optional[str] = None

    # Determine initial crawl queue. If root url is disallowed by robots.txt,
    # probe robots.txt rules for permitted alternative storefront paths before giving up.
    queue = [url]
    if not _is_robots_allowed(url):
        logger.info("[robots.txt] Target root path '%s' is disallowed. Searching for allowed alternative paths on %s...", url, domain)
        alt_paths = _find_allowed_candidate_paths(domain, scheme)
        if alt_paths:
            logger.info("[robots.txt] Discovered %d allowed alternative paths: %s", len(alt_paths), alt_paths)
            queue = alt_paths
        else:
            root_error = f"Site is live and reachable, but robots.txt policy disallows automated crawler access to target paths on {domain}."
            root_error_type = "ROBOTS_DISALLOWED"
            queue = []

    visited_urls: Set[str] = set()
    session = SafeRedirectSession(max_redirects=_MAX_REDIRECTS)

    while queue and len(visited_urls) < max_pages:
        curr_url = queue.pop(0)
        norm_url = curr_url.rstrip("/")
        if norm_url in visited_urls:
            continue
        visited_urls.add(norm_url)

        # Validate subpage URL
        is_safe, _, sec_err = validate_url_security(curr_url)
        if not is_safe:
            if curr_url == url or not pages_crawled:
                root_error = f"Security check failed for {curr_url}: {sec_err}"
                root_error_type = "SSRF_BLOCKED"
            continue

        # robots.txt compliance check for current subpage
        if not _is_robots_allowed(curr_url):
            logger.info("[crawler] Skipping robots.txt-disallowed URL: %s", curr_url)
            if (curr_url == url or not queue) and not pages_crawled:
                root_error = f"Robots.txt disallows automated crawler access on {domain}."
                root_error_type = "ROBOTS_DISALLOWED"
            continue

        # Per-domain rate limiting
        _enforce_rate_limit(domain)

        try:
            resp = session.get(curr_url, headers=_HEADERS, timeout=_PAGE_TIMEOUT, allow_redirects=True)
            resp.raise_for_status()
            
            content_type = resp.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                continue

            pages_crawled.append(curr_url)
            soup = BeautifulSoup(resp.text, "html.parser")

            if not main_title:
                main_title = _get_title(soup)
                main_description = _get_meta_description(soup)
                discovered_name = _extract_merchant_name(soup, domain, main_title)
                if discovered_name:
                    merchant_name = discovered_name

            page_text = _get_text(soup)
            combined_text.append(page_text)

            # Extract page images
            page_images, candidate_logo = _extract_rich_images(soup, curr_url)
            if not logo_url and candidate_logo:
                logo_url = candidate_logo
            certs = [img["src"] for img in page_images if img.get("asset_type") == "certificate"]
            banners = [img["src"] for img in page_images if img.get("asset_type") == "banner"]
            certificate_urls.extend(certs)
            banner_urls.extend(banners)

            for img_obj in page_images:
                src = img_obj.get("src", "")
                if src and src not in seen_image_urls:
                    seen_image_urls.add(src)
                    all_image_objects.append(img_obj)

            # Extract products
            extracted_p = _extract_products(soup, curr_url)
            for p in extracted_p:
                if not any(ep["name"] == p["name"] for ep in products):
                    products.append(p)

            # Discover internal links to prioritize key pages
            if len(visited_urls) < max_pages:
                sub_links = _discover_priority_links(soup, curr_url, domain)
                for sl in sub_links:
                    if sl.rstrip("/") not in visited_urls and sl not in queue:
                        queue.append(sl)

            # Social links
            for sl in _get_social_links(soup, curr_url):
                social_links.add(sl)

        except requests.exceptions.SSLError as e:
            logger.warning("[crawler] SSL Error on %s: %s", curr_url, e)
            if curr_url == url or not pages_crawled:
                root_error = f"SSL certificate verification failed for {domain}: {e}"
                root_error_type = "SSL_ERROR"
            continue
        except requests.exceptions.Timeout as e:
            logger.warning("[crawler] Timeout on %s: %s", curr_url, e)
            if curr_url == url or not pages_crawled:
                root_error = f"Connection timeout after {_PAGE_TIMEOUT}s connecting to {domain}."
                root_error_type = "TIMEOUT"
            continue
        except requests.exceptions.ConnectionError as e:
            err_str = str(e).lower()
            if "nameresolution" in err_str or "gaierror" in err_str or "getaddrinfo" in err_str or "not known" in err_str:
                root_error = f"DNS resolution failed: hostname '{domain}' could not be resolved."
                root_error_type = "DNS_RESOLUTION_FAILED"
            elif "refused" in err_str or "10061" in err_str:
                root_error = f"Connection refused by host '{domain}'."
                root_error_type = "CONNECTION_REFUSED"
            else:
                root_error = f"Network connection failed for '{domain}': {e}"
                root_error_type = "CONNECTION_FAILED"
            logger.warning("[crawler] Connection error on %s: %s", curr_url, root_error)
            continue
        except requests.exceptions.HTTPError as e:
            status_code = getattr(e.response, "status_code", 0) if hasattr(e, "response") else 0
            if curr_url == url or not pages_crawled:
                if status_code in (403, 429):
                    root_error = f"Target site's anti-bot protection blocked automated access (HTTP {status_code})."
                    root_error_type = "BOT_BLOCKED"
                else:
                    root_error = f"HTTP {status_code} error returned by {domain}."
                    root_error_type = f"HTTP_{status_code}" if status_code else "HTTP_ERROR"
            logger.warning("[crawler] HTTP error on %s: %s", curr_url, e)
            continue
        except requests.exceptions.TooManyRedirects as e:
            chain_details = getattr(session, "last_redirect_chain", [])
            chain_str = " -> ".join([f"{hop['url']} (status: {hop.get('status_code', 'redirect')})" for hop in chain_details]) if chain_details else str(e)
            logger.warning("[crawler] TooManyRedirects on %s. Redirect chain: %s", curr_url, chain_str)
            print(f"[CRAWLER_REDIRECT_LIMIT] TooManyRedirects on {curr_url}. Chain: {chain_str}")
            if curr_url == url or not pages_crawled:
                root_error = f"Redirect limit exceeded on {domain}: exceeded safety limit of {_MAX_REDIRECTS} hops ({chain_str})."
                root_error_type = "REDIRECT_LIMIT_EXCEEDED"
            continue
        except Exception as e:
            if curr_url == url or not pages_crawled:
                root_error = f"Failed to fetch {curr_url}: {e}"
                root_error_type = "CRAWL_FAILED"
            continue

    full_text = " ".join(combined_text)
    crawl_successful = len(pages_crawled) > 0
    crawl_status = "SUCCESS" if crawl_successful else (root_error_type or "CRAWL_FAILED")
    error_msg = None if crawl_successful else (root_error or "No pages could be successfully fetched from merchant domain.")

    classification = _classify_page_content(
        BeautifulSoup(combined_text[0] if combined_text else "", "html.parser") if crawl_successful else None,
        full_text,
        products,
        all_image_objects,
        domain
    ) if crawl_successful else {
        "site_category": "UNREACHABLE_SITE",
        "is_ecommerce": False,
        "confidence": 0.0,
        "summary": f"Unreachable domain ({domain}) — site could not be accessed",
        "indicators": [],
    }

    return {
        "url": url,
        "domain": domain,
        "merchant_name": merchant_name,
        "title": main_title,
        "description": main_description,
        "raw_text": full_text[:12000],
        "image_objects": all_image_objects,
        "image_urls": [img["src"] for img in all_image_objects],
        "products": products[:12],
        "logo_url": logo_url,
        "certificate_urls": list(set(certificate_urls)),
        "banner_urls": list(set(banner_urls)),
        "has_contact": _check_keyword(full_text, ["contact", "email", "support@", "phone", "tel:", "customer care", "helpdesk"]),
        "has_policy": _check_keyword(full_text, ["privacy policy", "terms of service", "terms & conditions", "refund policy", "return policy"]),
        "has_pricing": len(products) > 0 or _check_keyword(full_text, ["price", "pricing", "plans", "₹", "$", "€", "buy now", "cart", "checkout"]),
        "has_about": _check_keyword(full_text, ["about us", "our story", "who we are", "company profile", "about"]),
        "social_links": list(social_links),
        "pages_crawled": pages_crawled,
        "crawl_status": crawl_status,
        "crawl_successful": crawl_successful,
        "error": error_msg,
        "error_type": None if crawl_successful else crawl_status,
        "page_classification": classification,
        "is_ecommerce": classification.get("is_ecommerce", False),
        "blocked": False,
    }


def _extract_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return url


def _domain_to_name(domain: str) -> str:
    parts = domain.split(".")
    if parts:
        name = parts[0].replace("-", " ").replace("_", " ")
        return name.title()
    return "Merchant"


def _get_title(soup: BeautifulSoup) -> str:
    tag = soup.find("title")
    if tag:
        return tag.get_text(strip=True)
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"].strip()
    return ""


def _get_meta_description(soup: BeautifulSoup) -> str:
    for attr in [{"name": "description"}, {"property": "og:description"}, {"name": "twitter:description"}]:
        tag = soup.find("meta", attrs=attr)
        if tag and tag.get("content"):
            return tag["content"].strip()
    return ""


def _get_text(soup: BeautifulSoup) -> str:
    clone = BeautifulSoup(str(soup), "html.parser")
    for tag in clone(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()
    return " ".join(clone.get_text(separator=" ").split())


def _extract_merchant_name(soup: BeautifulSoup, domain: str, title: str) -> str:
    name = None
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            if not script.string:
                continue
            data = json.loads(script.string)
            if isinstance(data, list):
                data = data[0] if data else {}
            if isinstance(data, dict):
                stype = data.get("@type", "")
                if stype in ("Organization", "Store", "OnlineStore", "LocalBusiness", "Corporation", "Brand"):
                    if data.get("name"):
                        name = str(data["name"]).strip()
                        break
        except Exception:
            pass

    if not name:
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            name = og_site["content"].strip()

    if not name and title:
        for delim in [" | ", " - ", " — ", " : ", " · "]:
            if delim in title:
                parts = [p.strip() for p in title.split(delim) if p.strip()]
                for p in reversed(parts):
                    if len(p) <= 30 and not any(w in p.lower() for w in ["home", "official", "store", "buy", "shop", "online"]):
                        name = p
                        break
                if name:
                    break

    res_name = name or _domain_to_name(domain)
    return html.unescape(res_name)


def _extract_rich_images(soup: BeautifulSoup, base_url: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    image_objects: List[Dict[str, Any]] = []
    seen_urls = set()
    logo_candidate_url = None

    logo_tag = soup.find("img", attrs={"class": re.compile(r"logo|brand|header-logo|site-logo", re.I)}) or \
               soup.find("img", attrs={"id": re.compile(r"logo|brand", re.I)}) or \
               soup.find("img", attrs={"alt": re.compile(r"logo|brand", re.I)}) or \
               soup.find("a", attrs={"class": re.compile(r"brand|logo|navbar-brand", re.I)})

    if logo_tag:
        src = logo_tag.get("src") or (logo_tag.find("img") and logo_tag.find("img").get("src"))
        if src:
            full_logo = urljoin(base_url, src)
            if full_logo.startswith("http"):
                logo_candidate_url = full_logo

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or img.get("srcset", "").split(" ")[0]
        if not src:
            continue

        full_url = urljoin(base_url, src.strip())
        if not full_url.startswith("http") or full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        alt = img.get("alt", "").strip()
        img_title = img.get("title", "").strip()
        img_class = " ".join(img.get("class", [])) if isinstance(img.get("class"), list) else str(img.get("class", ""))
        img_id = str(img.get("id", ""))

        parents = [p.name for p in img.parents if p.name]
        is_in_header = any(p in ["header", "nav"] for p in parents) or "header" in img_class.lower()
        is_in_product = any(re.search(r"product|item|gallery|card|detail|showcase|catalog", p, re.I) for p in parents + [img_class, img_id])
        
        is_logo = is_in_header or bool(re.search(r"logo|brand", img_class + " " + img_id + " " + alt, re.I)) or (logo_candidate_url == full_url)
        is_cert = bool(re.search(r"cert|iso|badge|stamp|license|incorporation|registration|award|compliance", img_class + " " + img_id + " " + alt + " " + full_url, re.I))
        is_banner = bool(re.search(r"banner|hero|slider|carousel|showcase", img_class + " " + img_id + " " + full_url, re.I))

        # Determine asset classification
        if is_cert:
            asset_type = "certificate"
        elif is_logo:
            asset_type = "logo"
        elif is_banner:
            asset_type = "banner"
        else:
            asset_type = "product_image"

        image_objects.append({
            "src": full_url,
            "alt": alt,
            "title": img_title,
            "class": img_class,
            "asset_type": asset_type,
            "is_logo_candidate": is_logo,
            "is_product_candidate": is_in_product or (asset_type == "product_image"),
            "width": img.get("width"),
            "height": img.get("height"),
        })

    # Check OpenGraph Image
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        og_url = urljoin(base_url, og_img["content"].strip())
        if og_url.startswith("http") and og_url not in seen_urls:
            seen_urls.add(og_url)
            image_objects.insert(0, {
                "src": og_url,
                "alt": "OpenGraph Featured Visual",
                "title": "Featured Asset",
                "class": "og-image",
                "asset_type": "product_image",
                "is_logo_candidate": False,
                "is_product_candidate": True,
                "width": None,
                "height": None,
            })

    return image_objects, logo_candidate_url


def _discover_priority_links(soup: BeautifulSoup, base_url: str, domain: str) -> List[str]:
    priority_keywords = ["about", "product", "shop", "item", "catalog", "contact", "terms", "policy", "privacy"]
    discovered = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if _extract_domain(full) != domain:
            continue
        path_lower = parsed.path.lower()
        if any(kw in path_lower for kw in priority_keywords):
            if full not in discovered:
                discovered.append(full)
    return discovered[:8]


def _extract_products(soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
    products: List[Dict[str, Any]] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            if not script.string:
                continue
            data = json.loads(script.string)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") == "Product":
                    p_name = item.get("name", "")
                    p_desc = item.get("description", "")
                    p_img = item.get("image", "")
                    if isinstance(p_img, list) and p_img:
                        p_img = p_img[0]
                    p_price = ""
                    offers = item.get("offers", {})
                    if isinstance(offers, dict):
                        p_price = str(offers.get("price", ""))
                    if p_name:
                        products.append({
                            "name": p_name,
                            "description": p_desc[:200] if p_desc else "",
                            "price": p_price,
                            "image_url": urljoin(base_url, p_img) if p_img else None,
                        })
        except Exception:
            pass
    return products[:10]


def _check_keyword(text: str, keywords: List[str]) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in keywords)


def _get_social_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    social_domains = ["facebook.com", "twitter.com", "x.com", "instagram.com", "linkedin.com", "youtube.com", "pinterest.com"]
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(sd in href.lower() for sd in social_domains):
            full = urljoin(base_url, href)
            if full not in links:
                links.append(full)
    return links
