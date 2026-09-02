"""
Unit tests for image manipulation forensics, ELA, gradient anomalies, and synthetic indicators.
"""

import sys
from pathlib import Path
from PIL import Image
import numpy as np
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from visual.manipulation import (
    compute_ela,
    compute_gradient_noise_anomaly,
    estimate_synthetic_suspicion,
    analyze_image_manipulation,
)


def test_compute_ela_output_shapes_and_bounds():
    """Verify ELA array shape and score bounds on synthetic test image."""
    img = Image.new("RGB", (64, 64), color="lightblue")
    ela_arr, score = compute_ela(img)

    assert isinstance(ela_arr, np.ndarray)
    assert ela_arr.shape == (64, 64, 3)
    assert 0.0 <= score <= 100.0


def test_compute_gradient_noise_anomaly():
    """Verify Laplacian gradient anomaly output map and score range."""
    img_cv = np.full((64, 64, 3), 128, dtype=np.uint8)
    norm_map, score = compute_gradient_noise_anomaly(img_cv)

    assert isinstance(norm_map, np.ndarray)
    assert norm_map.shape == (64, 64)
    assert 0.0 <= score <= 100.0


def test_estimate_synthetic_suspicion():
    """Verify synthetic suspicion estimator returns score and explanation string."""
    img_cv = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    score, explanation = estimate_synthetic_suspicion(img_cv)

    assert 0.0 <= score <= 100.0
    assert isinstance(explanation, str)
    assert len(explanation) > 0


def test_analyze_image_manipulation_full():
    """Verify composite manipulation analysis pipeline returns expected dictionary keys."""
    img = Image.new("RGB", (80, 80), color="white")
    results = analyze_image_manipulation(img)

    assert "manipulation_score" in results
    assert "risk_level" in results
    assert "ela_image" in results
    assert "gradient_map" in results
    assert "synthetic_score" in results
    assert "synthetic_desc" in results
    assert "suspicious_regions" in results
    assert "explanation" in results
    assert isinstance(results["suspicious_regions"], list)
