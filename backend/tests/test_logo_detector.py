"""
Unit tests for logo and brand consistency verification engine.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image
import numpy as np
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.logo_detector import verify_merchant_logo


def test_verify_logo_missing_inputs():
    """Verify that missing image or brand returns UNAVAILABLE status safely."""
    status, evidence = verify_merchant_logo(None, "https://store.com/logo.png", "Acme")
    assert status == "UNAVAILABLE"
    assert evidence is None

    img = Image.new("RGB", (32, 32))
    status, evidence = verify_merchant_logo(img, "https://store.com/logo.png", None)
    assert status == "UNAVAILABLE"
    assert evidence is None


@patch("services.logo_detector.resolve_verified_brand_logo")
def test_verify_logo_unregistered_brand(mock_resolve):
    """Verify unverified brand registry lookup returns UNAVAILABLE."""
    mock_resolve.return_value = ("UNAVAILABLE", None, None)
    img = Image.new("RGB", (32, 32))

    status, evidence = verify_merchant_logo(img, "https://store.com/logo.png", "CustomShop")
    assert status == "UNAVAILABLE"
    assert evidence is None


@patch("services.logo_detector.resolve_verified_brand_logo")
@patch("services.logo_detector.get_image_embedding")
@patch("services.logo_detector.compute_cosine_similarity")
def test_verify_logo_high_mismatch(mock_sim, mock_emb, mock_resolve):
    """Verify high mismatch (<0.60 similarity) generates appropriate evidence score."""
    ref_img = Image.new("RGB", (32, 32))
    mock_resolve.return_value = ("VERIFIED", ref_img, "Nike")
    mock_emb.return_value = np.zeros(768)
    mock_sim.return_value = 0.35  # Low similarity -> high mismatch score

    merchant_img = Image.new("RGB", (32, 32))
    status, evidence = verify_merchant_logo(merchant_img, "https://store.com/logo.png", "Nike")

    assert status == "VERIFIED"
    assert evidence is not None
    assert evidence["score"] == 65
    assert evidence["signal_type"] == "potential_logo_mismatch"
    assert "Nike" in evidence["explanation"]


@patch("services.logo_detector.resolve_verified_brand_logo")
@patch("services.logo_detector.get_image_embedding")
@patch("services.logo_detector.compute_cosine_similarity")
def test_verify_logo_strong_match(mock_sim, mock_emb, mock_resolve):
    """Verify strong match (>=0.78 similarity) assigns 0 mismatch score."""
    ref_img = Image.new("RGB", (32, 32))
    mock_resolve.return_value = ("VERIFIED", ref_img, "Apple")
    mock_emb.return_value = np.zeros(768)
    mock_sim.return_value = 0.94

    merchant_img = Image.new("RGB", (32, 32))
    status, evidence = verify_merchant_logo(merchant_img, "https://store.com/logo.png", "Apple")

    assert status == "VERIFIED"
    assert evidence is not None
    assert evidence["score"] == 0
    assert "matches verified official Apple" in evidence["explanation"]
