"""
image_extractor.py — Downloads images from URLs and returns PIL Images.
Handles timeouts, bad formats, and redirects gracefully.
"""

from __future__ import annotations

import io
from typing import List, Optional, Tuple

import requests
from PIL import Image


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
_TIMEOUT = 8


def download_image(url: str) -> Optional[Image.Image]:
    """Download a single image URL and return a PIL Image, or None on failure."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT, stream=True)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "image" not in content_type and not url.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")
        ):
            return None
        data = resp.content
        img = Image.open(io.BytesIO(data)).convert("RGB")
        return img
    except Exception:
        return None


def download_images(urls: List[str], max_images: int = 10) -> List[Tuple[str, Image.Image]]:
    """
    Download up to `max_images` images from the provided URLs.

    Returns
    -------
    List of (url, PIL Image) tuples for successfully downloaded images.
    """
    results: List[Tuple[str, Image.Image]] = []
    for url in urls[:max_images]:
        img = download_image(url)
        if img is not None:
            results.append((url, img))
    return results
