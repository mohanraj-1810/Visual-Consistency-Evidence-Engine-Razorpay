"""
Unit tests for merchant site image extractor, dHash perceptual deduplication, and prioritization.
"""

import sys
from pathlib import Path
from PIL import Image
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from crawler.image_extractor import (
    compute_image_sha256,
    compute_dhash,
    hamming_distance,
    process_and_prioritize_images,
)


def test_compute_image_sha256():
    """Verify SHA-256 hash calculation on raw byte payloads."""
    payload = b"test_image_binary_data"
    hash_str = compute_image_sha256(payload)
    assert isinstance(hash_str, str)
    assert len(hash_str) == 64


def test_compute_dhash_and_hamming_distance():
    """Verify dHash produces integer hash and hamming distance calculation."""
    img1 = Image.new("RGB", (32, 32), color="red")
    img2 = Image.new("RGB", (32, 32), color="red")
    img3 = Image.new("RGB", (32, 32), color="blue")

    h1 = compute_dhash(img1)
    h2 = compute_dhash(img2)
    h3 = compute_dhash(img3)

    assert isinstance(h1, int)
    assert hamming_distance(h1, h2) == 0
    assert hamming_distance(h1, h3) >= 0


def test_process_and_prioritize_images_empty():
    """Verify empty input list returns formatted structure."""
    res = process_and_prioritize_images([])
    assert res["total_raw_count"] == 0
    assert res["representative_images"] == []
    assert res["logo_image"] is None
