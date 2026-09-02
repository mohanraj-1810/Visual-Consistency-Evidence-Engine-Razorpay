"""
Unit tests for visual catalog image reuse detection.
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

from visual.image_reuse import (
    load_reference_dataset,
    analyze_image_reuse,
    analyze_multiple_images_reuse,
)


def test_load_reference_dataset_nonexistent(tmp_path):
    """Verify loading from non-existent path safely returns empty dict."""
    non_existent = tmp_path / "does_not_exist"
    res = load_reference_dataset(non_existent)
    assert res == {}


@patch("visual.image_reuse.get_image_embedding")
def test_load_reference_dataset_valid_files(mock_emb, tmp_path):
    """Verify image embeddings are computed and cached from directory."""
    ref_dir = tmp_path / "ref"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "item1.png").touch()
    (ref_dir / "item2.jpg").touch()
    (ref_dir / "ignore.txt").touch()

    mock_emb.return_value = np.zeros(768)

    db = load_reference_dataset(ref_dir)
    assert len(db) == 2
    assert "item1.png" in db
    assert "item2.jpg" in db
    assert "ignore.txt" not in db


@patch("visual.image_reuse.load_reference_dataset")
@patch("visual.image_reuse.get_image_embedding")
@patch("visual.image_reuse.compute_cosine_similarity")
def test_analyze_image_reuse_high_risk(mock_sim, mock_emb, mock_load):
    """Verify high similarity creates HIGH risk level and explanation."""
    mock_load.return_value = {
        "catalog_shirt.jpg": (np.zeros(768), "/path/to/catalog_shirt.jpg")
    }
    mock_emb.return_value = np.zeros(768)
    mock_sim.return_value = 0.92

    test_img = Image.new("RGB", (32, 32))
    res = analyze_image_reuse(test_img)

    assert res["similarity"] == 0.92
    assert res["risk_level"] == "HIGH"
    assert res["reference_filename"] == "catalog_shirt.jpg"
    assert "Potential visual reuse detected" in res["explanation"]


@patch("visual.image_reuse.analyze_image_reuse")
def test_analyze_multiple_images_reuse(mock_analyze):
    """Verify batch processing over multiple merchant images."""
    mock_analyze.return_value = {
        "similarity": 0.88,
        "reference_filename": "ref.jpg",
        "reference_path": "/ref.jpg",
        "risk_level": "HIGH",
        "explanation": "Reuse detected",
        "all_matches": [],
    }

    images = [Image.new("RGB", (10, 10)), Image.new("RGB", (10, 10))]
    res = analyze_multiple_images_reuse(images)

    assert res["max_similarity"] == 0.88
    assert res["risk_level"] == "HIGH"
    assert len(res["findings"]) == 2
