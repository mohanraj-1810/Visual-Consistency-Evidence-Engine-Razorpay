"""
crawler/image_extractor.py — Scalable Visual Asset Extraction, Classification,
and Prioritization for Merchant Websites.
Categorizes assets into product_image, logo, certificate, banner, and enforces strict limits.
"""

from __future__ import annotations

import io
import re
import hashlib
from typing import List, Dict, Tuple, Optional, Any
from urllib.parse import urlparse

import requests
from PIL import Image
import numpy as np

from crawler.ssrf_validator import validate_url_security


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 (Razorpay-Visual-Risk-Engine/2.0)"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}
_TIMEOUT = 8
_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB limit
_MAX_DIMENSION = 4096                # Max width / height limit


def compute_image_sha256(data: bytes) -> str:
    """Computes SHA-256 hash of raw image bytes for tamper-proof deduplication and caching."""
    return hashlib.sha256(data).hexdigest()


def download_image(url: str) -> Optional[Tuple[Image.Image, str, bytes]]:
    """
    Downloads an image URL with SSRF protection, size caps, and format verification.
    Returns (PIL.Image, sha256_hash, raw_bytes) or None on failure.
    """
    if not url or not url.startswith(("http://", "https://")):
        return None

    is_safe, _, _ = validate_url_security(url)
    if not is_safe:
        return None

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT, stream=True)
        resp.raise_for_status()

        # Check content length header if present
        cl = resp.headers.get("Content-Length")
        if cl and int(cl) > _MAX_FILE_BYTES:
            return None

        # Read streaming bytes safely
        data = io.BytesIO()
        total_read = 0
        for chunk in resp.iter_content(chunk_size=65536):
            total_read += len(chunk)
            if total_read > _MAX_FILE_BYTES:
                return None
            data.write(chunk)

        raw_bytes = data.getvalue()
        if len(raw_bytes) < 150:
            return None

        raw_img = Image.open(io.BytesIO(raw_bytes))
        if raw_img.mode in ("RGBA", "LA") or (raw_img.mode == "P" and "transparency" in raw_img.info):
            img = raw_img.convert("RGBA").convert("RGB")
        else:
            img = raw_img.convert("RGB")

        w, h = img.size
        if w > _MAX_DIMENSION or h > _MAX_DIMENSION:
            img.thumbnail((_MAX_DIMENSION, _MAX_DIMENSION), Image.Resampling.LANCZOS)

        sha_hash = compute_image_sha256(raw_bytes)
        return img, sha_hash, raw_bytes
    except Exception:
        return None


def compute_dhash(image: Image.Image, hash_size: int = 8) -> int:
    """Computes a 64-bit difference hash (dHash) for fast perceptual deduplication."""
    try:
        resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        pixels = np.asarray(resized).flatten()
        diff = []
        for row in range(hash_size):
            for col in range(hash_size):
                idx = row * (hash_size + 1) + col
                diff.append(pixels[idx] > pixels[idx + 1])
        decimal_val = 0
        for bit in diff:
            decimal_val = (decimal_val << 1) | int(bit)
        return decimal_val
    except Exception:
        return 0


def hamming_distance(hash1: int, hash2: int) -> int:
    x = hash1 ^ hash2
    dist = 0
    while x > 0:
        dist += x & 1
        x >>= 1
    return dist


def process_and_prioritize_images(
    image_objects: List[Dict[str, Any]],
    merchant_name: str = "",
    max_representatives: int = 8,
) -> Dict[str, Any]:
    """
    Filters, deduplicates, and extracts up to `max_representatives` key assets
    categorized as product_image, logo, certificate, or banner.
    """
    total_raw = len(image_objects)
    if not image_objects:
        return {
            "representative_images": [],
            "logo_image": None,
            "logo_metadata": None,
            "certificate_images": [],
            "banner_images": [],
            "total_raw_count": 0,
            "filtered_count": 0,
            "deduplicated_count": 0,
            "clusters_count": 0,
        }

    # Step 1: Filter junk
    candidate_meta: List[Dict[str, Any]] = []
    seen_urls = set()
    for item in image_objects:
        src = item.get("src", "")
        if not src or src in seen_urls:
            continue
        seen_urls.add(src)
        if is_useless_ui_image(item):
            continue
        candidate_meta.append(item)

    # Step 2: Download candidate images
    downloaded_items: List[Dict[str, Any]] = []
    candidate_meta.sort(key=lambda x: preliminary_priority_score(x), reverse=True)

    for item in candidate_meta[:30]:
        res = download_image(item["src"])
        if res is None:
            continue
        img, sha256_hash, raw_bytes = res
        w, h = img.size
        if w < 50 or h < 50:
            continue
        aspect = max(w / h, h / w)
        if aspect > 6.0 and item.get("asset_type") != "banner":
            continue

        dhash = compute_dhash(img)
        item_copy = dict(item)
        item_copy["image"] = img
        item_copy["sha256"] = sha256_hash
        item_copy["raw_bytes"] = raw_bytes
        item_copy["width"] = w
        item_copy["height"] = h
        item_copy["dhash"] = dhash
        item_copy["area"] = w * h
        downloaded_items.append(item_copy)

    # Step 3: Perceptual Deduplication & Clustering
    unique_items: List[Dict[str, Any]] = []
    clusters: List[List[Dict[str, Any]]] = []

    for item in downloaded_items:
        is_dup = False
        item_hash = item["dhash"]
        for cluster in clusters:
            rep_hash = cluster[0]["dhash"]
            if hamming_distance(item_hash, rep_hash) <= 4:
                cluster.append(item)
                is_dup = True
                break
        if not is_dup:
            clusters.append([item])
            unique_items.append(item)

    # Step 4: Asset Categorization and Selection
    logo_item = None
    cert_items: List[Dict[str, Any]] = []
    banner_items: List[Dict[str, Any]] = []
    product_items: List[Dict[str, Any]] = []

    for item in unique_items:
        atype = item.get("asset_type", "product_image")
        if atype == "logo" or item.get("is_logo_candidate"):
            if logo_item is None:
                logo_item = item
                continue
        elif atype == "certificate":
            cert_items.append(item)
            continue
        elif atype == "banner":
            banner_items.append(item)
            continue

        item["priority_score"] = calculate_image_priority_score(item, merchant_name)
        product_items.append(item)

    product_items.sort(key=lambda x: x.get("priority_score", 0.0), reverse=True)

    # Step 5: Compose balanced representative list up to max_representatives
    selected_assets: List[Tuple[Image.Image, Dict[str, Any]]] = []

    if logo_item:
        logo_item["asset_type"] = "logo"
        selected_assets.append((logo_item["image"], logo_item))

    for c in cert_items[:2]:
        c["asset_type"] = "certificate"
        selected_assets.append((c["image"], c))

    for b in banner_items[:1]:
        b["asset_type"] = "banner"
        selected_assets.append((b["image"], b))

    slots_remaining = max_representatives - len(selected_assets)
    for p in product_items[:slots_remaining]:
        p["asset_type"] = "product_image"
        p["search_query_hint"] = build_image_search_query(p, merchant_name)
        selected_assets.append((p["image"], p))

    logo_img = logo_item["image"] if logo_item else None

    return {
        "representative_images": selected_assets[:max_representatives],
        "logo_image": logo_img,
        "logo_metadata": logo_item,
        "certificate_images": [c["image"] for c in cert_items],
        "banner_images": [b["image"] for b in banner_items],
        "total_raw_count": total_raw,
        "filtered_count": total_raw - len(downloaded_items),
        "deduplicated_count": len(downloaded_items) - len(unique_items),
        "clusters_count": len(clusters),
    }


def is_useless_ui_image(item: Dict[str, Any]) -> bool:
    src = item.get("src", "").lower()
    cls = item.get("class", "").lower()
    if any(k in src for k in ["1x1", "pixel", "tracking", "analytics", "spacer", "blank.gif", "empty.png"]):
        return True
    if any(k in src or k in cls for k in ["icon", "arrow", "chevron", "star-rating", "spinner", "loader"]):
        if not item.get("is_logo_candidate"):
            return True
    if src.endswith((".svg", ".ico")) and not item.get("is_logo_candidate"):
        return True
    return False


def preliminary_priority_score(item: Dict[str, Any]) -> float:
    score = 10.0
    atype = item.get("asset_type")
    if atype == "logo":
        score += 60.0
    elif atype == "certificate":
        score += 55.0
    elif atype == "product_image":
        score += 45.0
    elif atype == "banner":
        score += 30.0
    if item.get("alt") and len(item["alt"]) > 4:
        score += 15.0
    return score


def calculate_image_priority_score(item: Dict[str, Any], merchant_name: str) -> float:
    score = 0.0
    w, h = item.get("width", 0), item.get("height", 0)
    area = w * h
    if area >= 90000:
        score += 35.0
    elif area >= 40000:
        score += 20.0

    if h > 0:
        aspect = w / h
        if 0.65 <= aspect <= 1.5:
            score += 25.0

    alt = item.get("alt", "")
    if alt and len(alt.strip()) > 3:
        score += 20.0
        if merchant_name and merchant_name.lower() in alt.lower():
            score += 10.0

    return score


def build_image_search_query(item: Dict[str, Any], merchant_name: str) -> str:
    alt = item.get("alt", "").strip()
    title = item.get("title", "").strip()
    filename = urlparse(item.get("src", "")).path.split("/")[-1]
    clean_filename = re.sub(r"\.(jpg|jpeg|png|webp|avif|gif)$", "", filename, flags=re.I)
    clean_filename = re.sub(r"[-_]", " ", clean_filename).strip()

    terms = []
    if alt and len(alt) > 3 and not any(k in alt.lower() for k in ["image", "photo", "img"]):
        terms.append(alt)
    elif title and len(title) > 3:
        terms.append(title)
    elif clean_filename and len(clean_filename) > 3:
        terms.append(clean_filename)

    if merchant_name and merchant_name.lower() not in " ".join(terms).lower():
        terms.append(merchant_name)

    return " ".join(terms).strip() if terms else f"{merchant_name} product photo"
