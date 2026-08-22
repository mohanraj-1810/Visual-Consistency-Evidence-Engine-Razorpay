"""
site_crawler.py — Fetches page text, rich image objects, product metadata,
and merchant company details from a given URL.
"""

from __future__ import annotations

import json
import re
import time
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any, Tuple

import requests
from bs4 import BeautifulSoup


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_TIMEOUT = 12  # seconds


def crawl_merchant(url: str) -> Dict[str, Any]:
    """
    Crawl a merchant URL and extract comprehensive structured metadata.

    Returns
    -------
    dict with keys:
        url, domain, merchant_name, title, description, raw_text,
        image_objects: List of dicts (src, alt, title, container, is_logo_candidate, width, height),
        image_urls: List[str],
        products: List of dicts (name, description, price, image_url),
        logo_url: Optional[str],
        has_contact: bool, has_policy: bool, has_pricing: bool, has_about: bool,
        social_links: List[str], error: Optional[str]
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    domain = _extract_domain(url)

    result: Dict[str, Any] = {
        "url": url,
        "domain": domain,
        "merchant_name": _domain_to_name(domain),
        "title": "",
        "description": "",
        "raw_text": "",
        "image_objects": [],
        "image_urls": [],
        "products": [],
        "logo_url": None,
        "has_contact": False,
        "has_policy": False,
        "has_pricing": False,
        "has_about": False,
        "social_links": [],
        "error": None,
    }

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        result["title"] = _get_title(soup)
        result["description"] = _get_meta_description(soup)
        result["raw_text"] = _get_text(soup)

        # 1. Auto-extract Merchant Name (JSON-LD, OpenGraph, Title, Brand tags)
        merchant_name = _extract_merchant_name(soup, domain, result["title"])
        if merchant_name:
            result["merchant_name"] = merchant_name

        # 2. Extract Rich Image Objects with contextual metadata
        image_objects, logo_url = _extract_rich_images(soup, url)
        result["image_objects"] = image_objects
        result["image_urls"] = [img["src"] for img in image_objects]
        result["logo_url"] = logo_url

        # 3. Extract Product Information (from schema.org or DOM containers)
        result["products"] = _extract_products(soup, url)

        # 4. Text & Compliance Signals (Checking page text, headings, and link URLs/anchors)
        links_data = [(a.get("href", "").lower(), a.get_text(strip=True).lower()) for a in soup.find_all("a")]
        
        result["has_contact"] = _check_keyword(
            result["raw_text"], ["contact", "email", "support@", "phone", "tel:", "customer care", "helpdesk", "get in touch", "call us"]
        ) or any(any(kw in href or kw in txt for kw in ["contact", "support", "help", "helpdesk", "reach-us", "get-in-touch"]) for href, txt in links_data)

        result["has_policy"] = _check_keyword(
            result["raw_text"], ["privacy policy", "terms of service", "terms & conditions", "refund", "return policy", "cancellation", "privacy", "legal", "terms of use"]
        ) or any(any(kw in href or kw in txt for kw in ["privacy", "terms", "legal", "policy", "refund", "returns", "compliance", "cookie"]) for href, txt in links_data)

        result["has_pricing"] = (
            len(result["products"]) > 0
            or _check_keyword(result["raw_text"], ["price", "pricing", "plans", "₹", "$", "€", "£", "add to cart", "buy now", "checkout", "usd", "inr", "subscribe"])
            or any(any(kw in href or kw in txt for kw in ["pricing", "plans", "pricing-plans", "buy", "shop", "store", "cart"]) for href, txt in links_data)
        )

        result["has_about"] = _check_keyword(
            result["raw_text"], ["about us", "our story", "who we are", "our mission", "company profile", "about", "overview", "company"]
        ) or any(any(kw in href or kw in txt for kw in ["about", "about-us", "who-we-are", "company", "our-story", "overview"]) for href, txt in links_data)

        result["social_links"] = _get_social_links(soup, url)

    except requests.exceptions.ConnectionError:
        result["error"] = "Could not connect to the merchant website. Check URL and internet connection."
    except requests.exceptions.Timeout:
        result["error"] = "Request timed out. The merchant site may be slow or unreachable."
    except requests.exceptions.HTTPError as e:
        result["error"] = f"HTTP error {e.response.status_code} when accessing the merchant site."
    except Exception as e:
        result["error"] = f"Error while crawling merchant site: {str(e)}"

    return result


# ── Internal Extraction Helpers ──────────────────────────────────────────────

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
    # Clone soup so we don't mutate original
    clone = BeautifulSoup(str(soup), "html.parser")
    for tag in clone(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()
    return " ".join(clone.get_text(separator=" ").split())[:8000]


def _extract_merchant_name(soup: BeautifulSoup, domain: str, title: str) -> str:
    """Extract merchant/brand name accurately from metadata, JSON-LD, or OpenGraph."""
    # 1. JSON-LD Schema.org Organization / Store
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
                if "@graph" in data and isinstance(data["@graph"], list):
                    for item in data["@graph"]:
                        if item.get("@type") in ("Organization", "Store", "OnlineStore", "WebSite"):
                            if item.get("name"):
                                return str(item["name"]).strip()
        except Exception:
            pass

    # 2. OpenGraph Site Name
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        return og_site["content"].strip()

    # 3. Clean Title (e.g., "Product Name | BrandName" or "BrandName - Official Store")
    if title:
        for delim in [" | ", " - ", " — ", " : ", " · "]:
            if delim in title:
                parts = [p.strip() for p in title.split(delim) if p.strip()]
                # Usually the brand is at the start or end
                for p in reversed(parts):
                    if len(p) <= 30 and not any(w in p.lower() for w in ["home", "official", "store", "buy", "shop", "online"]):
                        return p

    return _domain_to_name(domain)


def _extract_rich_images(soup: BeautifulSoup, base_url: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Extracts all images with rich contextual signals (alt, title, container type, dimensions).
    Also identifies the top candidate for brand logo.
    """
    image_objects: List[Dict[str, Any]] = []
    seen_urls = set()
    logo_candidate_url = None

    # Find logo candidate first
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

    # Extract all <img> tags
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or img.get("srcset", "").split(" ")[0]
        if not src:
            continue

        full_url = urljoin(base_url, src.strip())
        if not full_url.startswith("http"):
            continue

        # Skip data urls of spacers or tiny 1x1 base64
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        alt = img.get("alt", "").strip()
        img_title = img.get("title", "").strip()
        img_class = " ".join(img.get("class", [])) if isinstance(img.get("class"), list) else str(img.get("class", ""))
        img_id = str(img.get("id", ""))

        # Context analysis (parent tags)
        parents = [p.name for p in img.parents if p.name]
        is_in_header = any(p in ["header", "nav"] for p in parents) or "header" in img_class.lower()
        is_in_product = any(
            re.search(r"product|item|gallery|card|detail|showcase|catalog", p, re.I)
            for p in parents + [img_class, img_id]
        )
        is_logo = (
            is_in_header
            or bool(re.search(r"logo|brand", img_class + " " + img_id + " " + alt, re.I))
            or (logo_candidate_url == full_url)
        )

        width_attr = img.get("width")
        height_attr = img.get("height")

        image_objects.append({
            "src": full_url,
            "alt": alt,
            "title": img_title,
            "class": img_class,
            "is_logo_candidate": is_logo,
            "is_product_candidate": is_product_candidate_heuristic(full_url, alt, is_in_product, is_logo),
            "width": width_attr,
            "height": height_attr,
        })

    # Also check OpenGraph Image
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        og_url = urljoin(base_url, og_img["content"].strip())
        if og_url.startswith("http") and og_url not in seen_urls:
            seen_urls.add(og_url)
            image_objects.insert(0, {
                "src": og_url,
                "alt": "OpenGraph Featured Image",
                "title": "Featured Visual Asset",
                "class": "og-image",
                "is_logo_candidate": False,
                "is_product_candidate": True,
                "width": None,
                "height": None,
            })

    return image_objects, logo_candidate_url


def is_product_candidate_heuristic(url: str, alt: str, is_in_product: bool, is_logo: bool) -> bool:
    if is_logo:
        return False
    low_url = url.lower()
    low_alt = alt.lower()

    # Reject obvious non-products
    if any(k in low_url or k in low_alt for k in ["icon", "badge", "avatar", "banner", "button", "arrow", "social", "payment", "visa", "mastercard"]):
        return False

    if is_in_product:
        return True

    if any(k in low_url for k in ["product", "item", "catalog", "uploads", "wp-content/uploads", "cdn/shop", "images/products"]):
        return True

    if len(alt) > 5 and not any(k in low_alt for k in ["logo", "icon", "arrow", "banner"]):
        return True

    return False


def _extract_products(soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
    """Extract product titles, descriptions, and images from page DOM."""
    products: List[Dict[str, Any]] = []

    # 1. JSON-LD Products
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

    # 2. DOM Product Cards if JSON-LD yielded few/none
    if len(products) < 3:
        product_elements = soup.find_all(attrs={"class": re.compile(r"product-card|product-item|grid-item|product_item|shop-item", re.I)})
        for el in product_elements[:6]:
            title_tag = el.find(["h2", "h3", "h4", "a", "span"], attrs={"class": re.compile(r"title|name|heading", re.I)}) or el.find(["h2", "h3", "h4"])
            img_tag = el.find("img")
            price_tag = el.find(attrs={"class": re.compile(r"price|amount|cost", re.I)})

            if title_tag:
                name = title_tag.get_text(strip=True)
                if len(name) > 3:
                    img_src = None
                    if img_tag and img_tag.get("src"):
                        img_src = urljoin(base_url, img_tag["src"])
                    products.append({
                        "name": name,
                        "description": "",
                        "price": price_tag.get_text(strip=True) if price_tag else "",
                        "image_url": img_src,
                    })

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
