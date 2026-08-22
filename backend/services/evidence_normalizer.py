"""
services/evidence_normalizer.py — Normalizes Google Cloud Vision Web Detection
results into structured, explainable visual evidence objects.
Filters self-referencing domains and categorizes marketplace vs external web reuse.
"""

from __future__ import annotations

from urllib.parse import urlparse
from typing import Dict, List, Optional, Any


_KNOWN_MARKETPLACES = {
    "amazon.com", "amazon.in", "flipkart.com", "aliexpress.com", "ebay.com",
    "walmart.com", "alibaba.com", "etsy.com", "myntra.com", "ajio.com",
    "target.com", "shopee.com", "lazada.com", "temu.com", "shein.com"
}

_KNOWN_STOCK_SITES = {
    "shutterstock.com", "gettyimages.com", "freepik.com", "istockphoto.com",
    "unsplash.com", "pexels.com", "stock.adobe.com", "pixabay.com", "dreamstime.com"
}


def _extract_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def is_self_referencing_domain(target_domain: str, merchant_domain: Optional[str]) -> bool:
    """Checks if a matching URL belongs to the merchant's own domain or subdomains."""
    if not target_domain or not merchant_domain:
        return False
    td = target_domain.lower().replace("www.", "").strip()
    md = merchant_domain.lower().replace("www.", "").strip()
    return td == md or td.endswith("." + md) or md.endswith("." + td)


def is_marketplace_domain(domain: str) -> bool:
    """Determines if a domain is a known multi-vendor marketplace or e-commerce aggregator."""
    clean = domain.lower().replace("www.", "").strip()
    return any(clean == mp or clean.endswith("." + mp) for mp in _KNOWN_MARKETPLACES)


def is_stock_domain(domain: str) -> bool:
    """Determines if a domain is a known stock-photography repository."""
    clean = domain.lower().replace("www.", "").strip()
    return any(clean == st or clean.endswith("." + st) for st in _KNOWN_STOCK_SITES)


def normalize_web_detection_evidence(
    item_result: Dict[str, Any],
    merchant_domain: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Transforms raw web detection and asset metadata into a clean visual reuse evidence item.
    """
    meta = item_result.get("meta", {})
    web_data = item_result.get("web_detection", {})
    
    asset_url = meta.get("src", "")
    asset_type = meta.get("asset_type", "product_image")
    
    full_matches = web_data.get("full_matching_images", [])
    partial_matches = web_data.get("partial_matching_images", [])
    all_matched_images = full_matches + partial_matches
    
    raw_pages = web_data.get("pages_with_matching_images", [])
    
    # Filter self-referencing pages and collect external matched pages
    matched_pages: List[Dict[str, str]] = []
    seen_page_urls = set()

    for page in raw_pages:
        p_url = page.get("url", "")
        if not p_url or p_url in seen_page_urls:
            continue
        seen_page_urls.add(p_url)
        p_domain = _extract_domain(p_url)

        # Ignore self-domain
        if is_self_referencing_domain(p_domain, merchant_domain):
            continue

        matched_pages.append({
            "url": p_url,
            "domain": p_domain,
        })

    # If no external pages found but matched image URLs exist, synthesize domains
    if not matched_pages and all_matched_images:
        for img_url in all_matched_images:
            img_domain = _extract_domain(img_url)
            if img_domain and not is_self_referencing_domain(img_domain, merchant_domain):
                matched_pages.append({
                    "url": img_url,
                    "domain": img_domain,
                })

    has_external_matches = len(matched_pages) > 0 or len(all_matched_images) > 0

    if not has_external_matches:
        # Asset is unique to merchant
        return {
            "asset_url": asset_url,
            "asset_type": asset_type,
            "signal_type": "external_image_reuse",
            "score": 0,
            "matched_pages": [],
            "matched_images": [],
            "explanation": f"Unique asset. No external online web matches discovered for this {asset_type}.",
            "heatmap_url": None,
            "is_marketplace_only": False,
            "is_stock_only": False,
        }

    # Calculate reuse severity score
    is_marketplace = any(is_marketplace_domain(p["domain"]) for p in matched_pages)
    is_stock = any(is_stock_domain(p["domain"]) for p in matched_pages)

    if full_matches:
        base_score = 65 if (is_marketplace or is_stock) else 75
    elif partial_matches:
        base_score = 45 if (is_marketplace or is_stock) else 55
    else:
        base_score = 30

    matched_domains_str = ", ".join(list(set(p["domain"] for p in matched_pages))[:3])
    
    if is_marketplace:
        explanation = (
            f"Visual reuse observed across external marketplace/catalog listing(s) ({matched_domains_str}). "
            f"Evidence of multi-channel listing or catalog reuse."
        )
    elif is_stock:
        explanation = (
            f"Visual asset matches known stock photography repository ({matched_domains_str})."
        )
    else:
        explanation = (
            f"Potential external visual reuse discovered across third-party site(s) ({matched_domains_str})."
        )

    return {
        "asset_url": asset_url,
        "asset_type": asset_type,
        "signal_type": "external_image_reuse",
        "score": base_score,
        "matched_pages": matched_pages[:5],
        "matched_images": all_matched_images[:5],
        "explanation": explanation,
        "heatmap_url": None,  # Strict Safety Rule: Heatmaps are NEVER used for external image reuse
        "is_marketplace_only": is_marketplace and not any(not is_marketplace_domain(p["domain"]) for p in matched_pages),
        "is_stock_only": is_stock and not any(not is_stock_domain(p["domain"]) for p in matched_pages),
    }
