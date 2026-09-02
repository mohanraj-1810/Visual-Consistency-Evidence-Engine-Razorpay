"""
Unit tests for official verified brand logo resolver.
"""

import sys
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.verified_brand_resolver import resolve_verified_brand_logo


def test_resolve_brand_invalid_input():
    """Verify that None, non-string, or very short inputs return UNAVAILABLE."""
    assert resolve_verified_brand_logo(None) == ("UNAVAILABLE", None, None)
    assert resolve_verified_brand_logo("") == ("UNAVAILABLE", None, None)
    assert resolve_verified_brand_logo("   ") == ("UNAVAILABLE", None, None)
    assert resolve_verified_brand_logo("a") == ("UNAVAILABLE", None, None)


def test_resolve_brand_missing_directory(tmp_path):
    """Verify behavior when logos directory does not exist."""
    non_existent = tmp_path / "does_not_exist"
    with patch("services.verified_brand_resolver._LOGOS_DIR", non_existent):
        status, img, name = resolve_verified_brand_logo("Nike")
        assert status == "UNAVAILABLE"
        assert img is None
        assert name is None


def test_resolve_brand_matched(tmp_path):
    """Verify brand matching from mock directory with brand image."""
    logos_dir = tmp_path / "logos"
    logos_dir.mkdir(parents=True, exist_ok=True)
    test_img_path = logos_dir / "acme_corp.png"
    sample_img = Image.new("RGB", (32, 32), color="red")
    sample_img.save(test_img_path)

    with patch("services.verified_brand_resolver._LOGOS_DIR", logos_dir):
        status, img, name = resolve_verified_brand_logo("Acme Corp")
        assert status == "VERIFIED"
        assert isinstance(img, Image.Image)
        assert name == "acme_corp"

        # Check normalization (hyphens/underscores)
        status2, img2, name2 = resolve_verified_brand_logo("acme-corp")
        assert status2 == "VERIFIED"
        assert name2 == "acme_corp"


def test_resolve_brand_unmatched(tmp_path):
    """Verify uncatalogued brand returns UNAVAILABLE."""
    logos_dir = tmp_path / "logos"
    logos_dir.mkdir(parents=True, exist_ok=True)
    test_img_path = logos_dir / "brand_x.png"
    Image.new("RGB", (16, 16)).save(test_img_path)

    with patch("services.verified_brand_resolver._LOGOS_DIR", logos_dir):
        status, img, name = resolve_verified_brand_logo("Unknown Unregistered Store")
        assert status == "UNAVAILABLE"
        assert img is None
        assert name is None
