"""
Unit tests for visual risk scoring and multi-signal corroboration.
"""

import sys
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scoring.visual_score import (
    calculate_visual_risk_score,
    WEIGHTS,
)


def test_weights_sum_to_one():
    """Verify calibrated weights sum to 1.0."""
    total_weight = sum(WEIGHTS.values())
    assert pytest.approx(total_weight, 0.001) == 1.0


def test_calculate_visual_risk_score_own_brand_zero_reuse():
    """Verify own-brand candidate results in zero E1 score and low risk."""
    reuse_data = {
        "match_status": "NO_EXTERNAL_MATCH",
        "is_own_brand_candidate": True,
        "reuse_risk_score": 85.0,
    }
    logo_data = {"inconsistency_risk": 0.0}
    manip_data = {"manipulation_score": 5.0, "synthetic_score": 10.0}

    res = calculate_visual_risk_score(reuse_data, logo_data, manip_data, cross_identity_coherence=90.0)
    assert res["E1_score"] == 0.0
    assert res["risk_level"] == "LOW"
    assert res["corroboration_active"] is False


def test_calculate_visual_risk_score_multi_signal_corroboration():
    """Verify multiple severe signals trigger corroboration amplification."""
    reuse_data = {
        "match_status": "CORROBORATED_EXTERNAL_MATCH",
        "reuse_risk_score": 85.0,
        "e4_score": 80.0,
    }
    logo_data = {"inconsistency_risk": 75.0}
    manip_data = {"manipulation_score": 70.0, "synthetic_score": 60.0}

    res = calculate_visual_risk_score(reuse_data, logo_data, manip_data, cross_identity_coherence=30.0)
    assert res["corroboration_active"] is True
    assert res["risk_level"] == "HIGH"
    assert res["visual_risk_score"] >= 70.0
