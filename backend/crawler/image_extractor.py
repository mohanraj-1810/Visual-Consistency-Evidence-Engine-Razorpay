"""
image_extractor.py — Scalable Image Processing, Filtering, Deduplication,
Grouping, and Prioritization for Merchant Websites with 1000+ Images.
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


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}
_TIMEOUT = 8


# ── 1. Image Download Helper ──────────────────────────────────────────────────

def download_image(url: str) -> Optional[Image.Image]:
    """Download a single image URL and return a PIL Image in RGB, or None on failure."""
    if not url or not url.startswith(("http://", "https://")):
        return None
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT, stream=True)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "").lower()
        if "image" not in content_type and not url.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".avif", ".gif")
        ):
            return None
        data = resp.content
        if len(data) < 150:  # Ignore empty or microscopic payloads
            return None
        img = Image.open(io.BytesIO(data)).convert("RGB")
        return img
    except Exception:
        return None


# ── 2. Perceptual Difference Hashing (dHash) for Fast Deduplication ──────────

def compute_dhash(image: Image.Image, hash_size: int = 8) -> int:
    """
    Computes a 64-bit difference hash (dHash) for fast perceptual deduplication.
    Robust against minor scaling, format conversions, and compression artifacts.
    """
    try:
        # Resize to (hash_size + 1, hash_size) grayscale
        resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        pixels = list(resized.getdata())
        
        # Compare adjacent pixels in each row
        diff = []
        for row in range(hash_size):
            for col in range(hash_size):
                idx = row * (hash_size + 1) + col
                diff.append(pixels[idx] > pixels[idx + 1])
        
        # Convert boolean list to integer hash
        decimal_val = 0
        for bit in diff:
            decimal_val = (decimal_val << 1) | bit
        return decimal_val
    except Exception:
        return 0


def hamming_distance(hash1: int, hash2: int) -> int:
    """Calculate the Hamming distance between two integer hashes."""
    x = hash1 ^ hash2
    dist = 0
    while x > 0:
        dist += x & 1
        x >>= 1
    return dist


# ── 3. High-Volume Image Processing Pipeline ─────────────────────────────────

def process_and_prioritize_images(
    image_objects: List[Dict[str, Any]],
    merchant_name: str = "",
    max_representatives: int = 5,
) -> Dict[str, Any]:
    """
    Orchestrates the 5-stage image pipeline for 1000+ website images:
      Stage 1: Filter useless/tiny/UI images
      Stage 2: Deduplicate (exact URL + perceptual dHash)
      Stage 3: Group & Cluster visually similar images
      Stage 4: Prioritize high-value visual assets (products, main assets, logo)
      Stage 5: Select top representative images with search hints

    Returns
    -------
    dict with:
        representative_images: List of (PIL.Image, dict_metadata)
        logo_image: Optional[PIL.Image]
        logo_metadata: Optional[dict]
        total_raw_count: int
        filtered_count: int
        deduplicated_count: int
        clusters_count: int
    """
    total_raw = len(image_objects)
    if not image_objects:
        return {
            "representative_images": [],
            "logo_image": None,
            "logo_metadata": None,
            "total_raw_count": 0,
            "filtered_count": 0,
            "deduplicated_count": 0,
            "clusters_count": 0,
        }

    # ── Stage 1: Filter useless / tiny / UI images by heuristics ─────────────
    candidate_meta: List[Dict[str, Any]] = []
    seen_urls = set()

    for item in image_objects:
        src = item.get("src", "")
        if not src or src in seen_urls:
            continue
        seen_urls.add(src)

        # Discard UI junk based on URL, alt text, or class name
        if is_useless_ui_image(item):
            continue

        candidate_meta.append(item)

    # ── Stage 2: Download & Perceptual Filter ────────────────────────────────
    downloaded_items: List[Dict[str, Any]] = []
    # Cap candidate downloads to top 25 high-priority candidates to keep performance fast
    # Rank preliminary candidates so we download most promising first
    candidate_meta.sort(key=lambda x: preliminary_priority_score(x), reverse=True)

    for item in candidate_meta[:25]:
        img = download_image(item["src"])
        if img is None:
            continue

        w, h = img.size
        # Filter tiny images (< 60px) or banner slices (< 30px height) or extreme aspect ratios (> 5:1)
        if w < 50 or h < 50:
            continue
        aspect = max(w / h, h / w)
        if aspect > 6.0:  # thin decorative ribbon / banner line
            continue

        dhash = compute_dhash(img)
        item_copy = dict(item)
        item_copy["image"] = img
        item_copy["width"] = w
        item_copy["height"] = h
        item_copy["dhash"] = dhash
        item_copy["area"] = w * h
        downloaded_items.append(item_copy)

    # ── Stage 3: Perceptual Deduplication & Grouping / Clustering ───────────
    unique_items: List[Dict[str, Any]] = []
    clusters: List[List[Dict[str, Any]]] = []

    for item in downloaded_items:
        is_dup = False
        item_hash = item["dhash"]

        for cluster in clusters:
            rep_hash = cluster[0]["dhash"]
            # Hamming distance <= 5 implies nearly identical image variation
            if hamming_distance(item_hash, rep_hash) <= 5:
                cluster.append(item)
                is_dup = True
                break

        if not is_dup:
            clusters.append([item])
            unique_items.append(item)

    # ── Stage 4: Prioritize and Extract Logo vs Product Assets ───────────────
    logo_item = None
    product_items: List[Dict[str, Any]] = []

    for item in unique_items:
        if item.get("is_logo_candidate") and logo_item is None:
            # Verify logo dimensions (usually wider than tall or square, < 800px)
            if item["width"] <= 900 and item["height"] <= 600:
                logo_item = item
                continue

        # Score product / main visual priority
        item["priority_score"] = calculate_image_priority_score(item, merchant_name)
        product_items.append(item)

    # Sort product visuals descending by priority score
    product_items.sort(key=lambda x: x["priority_score"], reverse=True)

    # If logo wasn't identified from candidate flags, check if any small square/header visual could be logo
    if logo_item is None and product_items:
        for idx, p in enumerate(product_items):
            if p["area"] < 100000 and ("logo" in p.get("class", "").lower() or "logo" in p.get("alt", "").lower()):
                logo_item = p
                product_items.pop(idx)
                break

    # ── Stage 5: Select Representative Images with Rich Search Hints ─────────
    representative_images: List[Tuple[Image.Image, Dict[str, Any]]] = []

    for item in product_items[:max_representatives]:
        # Formulate optimal search query hint for online evidence search
        query_hint = build_image_search_query(item, merchant_name)
        item["search_query_hint"] = query_hint
        representative_images.append((item["image"], item))

    logo_img = logo_item["image"] if logo_item else None

    return {
        "representative_images": representative_images,
        "logo_image": logo_img,
        "logo_metadata": logo_item,
        "total_raw_count": total_raw,
        "filtered_count": total_raw - len(downloaded_items),
        "deduplicated_count": len(downloaded_items) - len(unique_items),
        "clusters_count": len(clusters),
    }


# ── Heuristic Utilities ──────────────────────────────────────────────────────

def is_useless_ui_image(item: Dict[str, Any]) -> bool:
    """Checks if an image is obviously UI decoration, icon, or tracking pixel."""
    src = item.get("src", "").lower()
    alt = item.get("alt", "").lower()
    cls = item.get("class", "").lower()

    # Tracking pixels / analytics
    if any(k in src for k in ["1x1", "pixel", "tracking", "analytics", "badge", "spacer", "blank.gif", "empty.png"]):
        return True

    # Common UI elements
    if any(k in src or k in cls for k in ["icon", "arrow", "chevron", "star-rating", "social", "payment-icons", "cart-icon", "spinner", "loader"]):
        if not item.get("is_logo_candidate"):
            return True

    # SVGs or favicons
    if src.endswith((".svg", ".ico")) and not item.get("is_logo_candidate"):
        return True

    return False


def preliminary_priority_score(item: Dict[str, Any]) -> float:
    """Quick score before downloading image."""
    score = 10.0
    if item.get("is_product_candidate"):
        score += 50.0
    if item.get("is_logo_candidate"):
        score += 40.0
    if item.get("alt") and len(item["alt"]) > 4:
        score += 20.0
    if item.get("width") and item.get("height"):
        try:
            w, h = int(item["width"]), int(item["height"])
            if w >= 200 and h >= 200:
                score += 30.0
        except Exception:
            pass
    return score


def calculate_image_priority_score(item: Dict[str, Any], merchant_name: str) -> float:
    """Calculate rich priority score based on size, aspect ratio, alt text, and container."""
    score = 0.0

    # 1. Size & Resolution (Prefer high-res product photos: 300x300 to 1200x1200)
    w, h = item.get("width", 0), item.get("height", 0)
    area = w * h
    if area >= 90000:   # >= 300x300
        score += 35.0
    elif area >= 40000: # >= 200x200
        score += 20.0

    # 2. Aspect Ratio (Product photos usually 1:1, 4:3, 3:4, 16:9)
    if h > 0:
        aspect = w / h
        if 0.65 <= aspect <= 1.5:
            score += 25.0
        elif 0.5 <= aspect <= 2.0:
            score += 15.0

    # 3. Product context from DOM / schema
    if item.get("is_product_candidate"):
        score += 30.0

    # 4. Alt text quality
    alt = item.get("alt", "")
    if alt and len(alt.strip()) > 3:
        score += 20.0
        if merchant_name and merchant_name.lower() in alt.lower():
            score += 10.0

    # 5. Filename richness
    filename = urlparse(item.get("src", "")).path.split("/")[-1].lower()
    if any(k in filename for k in ["product", "item", "watch", "shoe", "bag", "shirt", "phone", "craft", "pottery", "detail"]):
        score += 15.0

    return score


def build_image_search_query(item: Dict[str, Any], merchant_name: str) -> str:
    """Formulate an accurate online search query using alt text, filename, and merchant context."""
    alt = item.get("alt", "").strip()
    title = item.get("title", "").strip()
    filename = urlparse(item.get("src", "")).path.split("/")[-1]
    
    # Remove file extension and clean separators
    clean_filename = re.sub(r"\.(jpg|jpeg|png|webp|avif|gif)$", "", filename, flags=re.I)
    clean_filename = re.sub(r"[-_]", " ", clean_filename)
    # Strip random hash codes like "1200x1200_a89b7c"
    clean_filename = re.sub(r"\b[0-9a-f]{6,}\b|\b\d+x\d+\b", "", clean_filename).strip()

    terms = []
    if alt and len(alt) > 3 and not any(k in alt.lower() for k in ["image", "photo", "picture", "img"]):
        terms.append(alt)
    elif title and len(title) > 3:
        terms.append(title)
    elif clean_filename and len(clean_filename) > 3:
        terms.append(clean_filename)

    if merchant_name and merchant_name.lower() not in " ".join(terms).lower():
        terms.append(merchant_name)

    query = " ".join(terms).strip()
    return query if query else f"{merchant_name} product photo"


# Legacy download compatibility helper for unit tests
def download_images(urls: List[str], max_images: int = 10) -> List[Tuple[str, Image.Image]]:
    """Legacy helper for downloading images from a list of URLs."""
    results: List[Tuple[str, Image.Image]] = []
    for url in urls[:max_images]:
        img = download_image(url)
        if img is not None:
            results.append((url, img))
    return results
