"""
site_crawler.py — Fetches page text, image URLs, and basic merchant metadata
from a given URL. Returns a structured dict so the rest of the pipeline
can work without caring about how the data was collected.
"""

from __future__ import annotations

import re
import time
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_TIMEOUT = 10  # seconds


def crawl_merchant(url: str) -> Dict:
    """
    Crawl a merchant URL and return structured metadata.

    Returns
    -------
    dict with keys:
        url, domain, title, description, raw_text,
        image_urls, has_contact, has_policy, has_pricing,
        has_about, social_links, error
    """
    result: Dict = {
        "url": url,
        "domain": _extract_domain(url),
        "title": "",
        "description": "",
        "raw_text": "",
        "image_urls": [],
        "has_contact": False,
        "has_policy": False,
        "has_pricing": False,
        "has_about": False,
        "social_links": [],
        "error": None,
    }

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        result["title"] = _get_title(soup)
        result["description"] = _get_meta_description(soup)
        result["raw_text"] = _get_text(soup)
        result["image_urls"] = _get_image_urls(soup, url)
        result["has_contact"] = _check_keyword(result["raw_text"], ["contact", "email", "phone", "tel:"])
        result["has_policy"] = _check_keyword(result["raw_text"], ["privacy policy", "terms", "refund", "return policy"])
        result["has_pricing"] = _check_keyword(result["raw_text"], ["price", "₹", "$", "buy", "shop", "cart"])
        result["has_about"] = _check_keyword(result["raw_text"], ["about us", "our story", "who we are"])
        result["social_links"] = _get_social_links(soup, url)

    except requests.exceptions.ConnectionError:
        result["error"] = "Could not connect to the merchant website. Check the URL and your internet connection."
    except requests.exceptions.Timeout:
        result["error"] = "Request timed out. The merchant site may be slow or unreachable."
    except requests.exceptions.HTTPError as e:
        result["error"] = f"HTTP error {e.response.status_code} when accessing the merchant site."
    except Exception as e:
        result["error"] = f"Unexpected error while crawling: {str(e)}"

    return result


# ── helpers ──────────────────────────────────────────────────────────────────

def _extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return url


def _get_title(soup: BeautifulSoup) -> str:
    tag = soup.find("title")
    return tag.get_text(strip=True) if tag else ""


def _get_meta_description(soup: BeautifulSoup) -> str:
    tag = soup.find("meta", attrs={"name": "description"})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return ""


def _get_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ").split())[:5000]


def _get_image_urls(soup: BeautifulSoup, base_url: str) -> List[str]:
    urls: List[str] = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        full = urljoin(base_url, src)
        if full.startswith("http") and full not in urls:
            urls.append(full)
    return urls[:20]  # cap at 20


def _check_keyword(text: str, keywords: List[str]) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in keywords)


def _get_social_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    social_domains = ["facebook", "twitter", "instagram", "linkedin", "youtube", "pinterest"]
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(sd in href for sd in social_domains):
            links.append(href)
    return list(set(links))
