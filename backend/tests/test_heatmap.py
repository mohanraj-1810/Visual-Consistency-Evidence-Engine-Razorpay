"""
Unit tests for explainable visual forensic heatmap generator.
"""

import sys
from pathlib import Path
from PIL import Image
import numpy as np
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from visual.heatmap import generate_forensic_heatmap


def test_generate_forensic_heatmap_basic():
    """Verify output shape and RGB channels when generating heatmap from PIL Image."""
    img = Image.new("RGB", (64, 64), color="white")
    overlay = generate_forensic_heatmap(img)

    assert isinstance(overlay, np.ndarray)
    assert overlay.shape == (64, 64, 3)


def test_generate_forensic_heatmap_with_boxes_and_signals():
    """Verify heatmap overlays ELA, gradient maps, and suspicious bounding boxes."""
    img = Image.new("RGB", (100, 100), color="blue")
    ela = np.zeros((100, 100, 3), dtype=np.uint8)
    grad = np.zeros((100, 100), dtype=np.uint8)
    boxes = [(10, 10, 30, 30)]

    overlay = generate_forensic_heatmap(
        img,
        ela_image=ela,
        gradient_map=grad,
        suspicious_boxes=boxes,
        alpha=0.5,
    )

    assert isinstance(overlay, np.ndarray)
    assert overlay.shape == (100, 100, 3)


def test_generate_forensic_heatmap_numpy_input():
    """Verify heatmap accepts raw numpy RGB arrays directly."""
    img_arr = np.zeros((48, 48, 3), dtype=np.uint8)
    overlay = generate_forensic_heatmap(img_arr)

    assert isinstance(overlay, np.ndarray)
    assert overlay.shape == (48, 48, 3)
