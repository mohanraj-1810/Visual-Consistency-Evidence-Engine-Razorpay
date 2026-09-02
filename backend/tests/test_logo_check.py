"""
Unit tests for visual brand logo consistency checker.
"""

import sys
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import numpy as np
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from visual.logo_check import (
    load_verified_logos,
    check_logo_consistency,
)


def test_load_verified_logos_nonexistent(tmp_path):
    """Verify loading from non-existent directory safely returns empty dictionary."""
    non_existent = tmp_path / "does_not_exist"
    assert load_verified_logos(non_existent) == {}


def test_check_logo_consistency_empty_registry(tmp_path):
    """Verify empty logo directory produces neutral low risk."""
    empty_dir = tmp_path / "empty_logos"
    empty_dir.mkdir(parents=True, exist_ok=True)

    test_img = Image.new("RGB", (32, 32))
    res = check_logo_consistency(test_img, claimed_brand="Nike", logos_dir=empty_dir)

    assert res["similarity"] == 1.0
    assert res["risk_level"] == "LOW"
    assert res["inconsistency_risk"] == 0.0


@patch("visual.logo_check.load_verified_logos")
@patch("visual.logo_check.get_image_embedding")
def test_check_logo_consistency_unmatched_brand(mock_emb, mock_load):
    """Verify uncatalogued brand produces neutral low risk."""
    mock_load.return_value = {
        "apple_logo.png": (np.zeros(768), "/path/to/apple_logo.png")
    }
    mock_emb.return_value = np.zeros(768)

    test_img = Image.new("RGB", (32, 32))
    res = check_logo_consistency(test_img, claimed_brand="UnregisteredStore")

    assert res["risk_level"] == "LOW"
    assert "No registered brand reference logo available" in res["explanation"]


@patch("visual.logo_check.load_verified_logos")
@patch("visual.logo_check.get_image_embedding")
@patch("visual.logo_check.compute_cosine_similarity")
def test_check_logo_consistency_divergence(mock_sim, mock_emb, mock_load):
    """Verify low similarity against registered brand produces HIGH risk."""
    mock_load.return_value = {
        "nike_swoosh.png": (np.zeros(768), "/path/to/nike_swoosh.png")
    }
    mock_emb.return_value = np.zeros(768)
    mock_sim.return_value = 0.35

    test_img = Image.new("RGB", (32, 32))
    res = check_logo_consistency(test_img, claimed_brand="Nike")

    assert res["risk_level"] == "HIGH"
    assert res["similarity"] == 0.35
    assert res["inconsistency_risk"] == 65.0
    assert "shows low visual similarity" in res["explanation"]
