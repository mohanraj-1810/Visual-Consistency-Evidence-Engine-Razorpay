"""
crawler/site_crawler.py — Multi-page SSRF-safe Merchant Crawler.
Crawls up to 5 key merchant website pages, extracts metadata, product visuals,
brand logos, certificates, and header banners with strict security controls.
"""

from __future__ import annotations

import json
import re
import time
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any, Tuple, Set

import requests
from bs4 import BeautifulSoup

from crawler.ssrf_validator import validate_url_security, is_ip_blocked


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 (Razorpay-Visual-Risk-Engine/2.0)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_PAGE_TIMEOUT = 8  # seconds per page
_MAX_PAGES = 5      # Maximum pages crawled per site
_MAX_REDIRECTS = 3  # Maximum allowed redirects


class SafeRedirectSession(requests.Session):
    """Requests session enforcing SSRF validation across all redirect hops."""
    def __init__(self, max_redirects: int = _MAX_REDIRECTS):
        super().__init__()
        self.max_redirect_count = max_redirects

    def resolve_redirects(self, resp, req, stream=False, timeout=None, verify=True, cert=None, proxies=None, yield_requests=False, **adapter_kwargs):
        redirect_count = 0
        for redirect_req in super().resolve_redirects(resp, req, stream=stream, timeout=timeout, verify=verify, cert=cert, proxies=proxies, yield_requests=True, **adapter_kwargs):
            redirect_count += 1
            if redirect_count > self.max_redirect_count:
                raise requests.exceptions.TooManyRedirects(f"Exceeded maximum allowed redirects ({self.max_redirect_count}).")
            
            is_valid, ip_addr, err_msg = validate_url_security(redirect_req.url)
            if not is_valid:
                raise requests.exceptions.RequestException(f"SSRF validation blocked redirect to '{redirect_req.url}': {err_msg}")
            
            if yield_requests:
                yield redirect_req
            else:
                resp = self.send(redirect_req, stream=stream, timeout=timeout, verify=verify, cert=cert, proxies=proxies, **adapter_kwargs)
                yield resp


def crawl_merchant(url: str, max_pages: int = _MAX_PAGES) -> Dict[str, Any]:
    """
    Crawls up to `max_pages` of a merchant website starting from `url` in an SSRF-safe manner.
    Discovers key navigation pages (Home, About, Products, Contact, Terms/Policy).
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    is_valid, ip_addr, err_msg = validate_url_security(url)
    if not is_valid:
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
            "error": f"Security validation failed: {err_msg}",
            "blocked": True,
        }

    domain = _extract_domain(url)
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

    queue = [url]
    visited_urls: Set[str] = set()
    session = SafeRedirectSession(max_redirects=_MAX_REDIRECTS)

    while queue and len(visited_urls) < max_pages:
        curr_url = queue.pop(0)
        norm_url = curr_url.rstrip("/")
        if norm_url in visited_urls:
            continue
        visited_urls.add(norm_url)

        # Validate subpage URL
        is_safe, _, _ = validate_url_security(curr_url)
        if not is_safe:
            continue

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

        except Exception:
            continue

    full_text = " ".join(combined_text)
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
        "error": None if pages_crawled else "No pages could be successfully fetched from merchant domain.",
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
                        return str(data["name"]).strip()
        except Exception:
            pass

    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        return og_site["content"].strip()

    if title:
        for delim in [" | ", " - ", " — ", " : ", " · "]:
            if delim in title:
                parts = [p.strip() for p in title.split(delim) if p.strip()]
                for p in reversed(parts):
                    if len(p) <= 30 and not any(w in p.lower() for w in ["home", "official", "store", "buy", "shop", "online"]):
                        return p

    return _domain_to_name(domain)


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
