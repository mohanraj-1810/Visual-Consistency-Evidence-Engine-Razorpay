"""
Unit tests for forensic manipulation analysis and heatmap generation service.
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

from services.forensic_heatmap import (
    image_to_base64_url,
    run_forensic_tampering_analysis,
)


def test_image_to_base64_url_inputs():
    """Verify base64 encoding handles None, PIL, and various numpy dimensions."""
    assert image_to_base64_url(None) is None

    # PIL Image
    pil_img = Image.new("RGB", (16, 16), color="green")
    res_pil = image_to_base64_url(pil_img)
    assert res_pil is not None
    assert res_pil.startswith("data:image/png;base64,")

    # Grayscale 2D array
    arr_2d = np.ones((16, 16), dtype=np.uint8) * 128
    res_2d = image_to_base64_url(arr_2d)
    assert res_2d is not None
    assert res_2d.startswith("data:image/png;base64,")

    # RGBA 3D array
    arr_rgba = np.zeros((16, 16, 4), dtype=np.uint8)
    res_rgba = image_to_base64_url(arr_rgba)
    assert res_rgba is not None
    assert res_rgba.startswith("data:image/png;base64,")


def test_run_forensic_tampering_analysis_none_image():
    """Verify that None input returns score 0 and None evidence."""
    score, evidence = run_forensic_tampering_analysis(None, "https://example.com/doc.png")
    assert score == 0
    assert evidence is None


@patch("services.forensic_heatmap.analyze_image_manipulation")
@patch("services.forensic_heatmap.generate_forensic_heatmap")
def test_run_forensic_tampering_analysis_elevated_score(mock_heatmap, mock_manip):
    """Verify that high tampering score generates explanation and embeds heatmap."""
    mock_manip.return_value = {
        "manipulation_score": 72.0,
        "ela_image": np.zeros((32, 32, 3), dtype=np.uint8),
        "gradient_map": np.zeros((32, 32), dtype=np.uint8),
        "suspicious_regions": [{"bbox": [5, 5, 20, 20], "score": 0.8}],
    }
    mock_heatmap.return_value = Image.new("RGB", (32, 32), color="red")

    test_img = Image.new("RGB", (32, 32))
    score, evidence = run_forensic_tampering_analysis(
        test_img,
        asset_url="https://shop.com/cert.png",
        asset_type="certificate",
    )

    assert score == 72
    assert evidence is not None
    assert evidence["score"] == 72
    assert evidence["signal_type"] == "manipulation"
    assert "Digital manipulation indicators detected in certificate" in evidence["explanation"]
    assert evidence["heatmap_url"] is not None
    assert evidence["heatmap_url"].startswith("data:image/png;base64,")


@patch("services.forensic_heatmap.analyze_image_manipulation")
def test_run_forensic_tampering_analysis_clean(mock_manip):
    """Verify that clean image produces score < 35 with no heatmap URL."""
    mock_manip.return_value = {
        "manipulation_score": 12.0,
        "ela_image": None,
        "gradient_map": None,
        "suspicious_regions": [],
    }

    test_img = Image.new("RGB", (32, 32))
    score, evidence = run_forensic_tampering_analysis(
        test_img,
        asset_url="https://shop.com/clean.png",
        asset_type="invoice",
    )

    assert score == 12
    assert evidence is not None
    assert evidence["score"] == 12
    assert evidence["heatmap_url"] is None
    assert "No digital manipulation" in evidence["explanation"]
