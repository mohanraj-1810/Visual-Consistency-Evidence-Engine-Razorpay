"""
Unit tests for visual risk scoring and multi-signal corroboration engine.
"""

import sys
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.visual_risk_scorer import calculate_visual_risk


def test_calculate_visual_risk_empty():
    """Verify empty evidence list produces score 0 and LOW risk."""
    score, level, action = calculate_visual_risk([])
    assert score == 0
    assert level == "LOW"
    assert action == "NORMAL_FLOW"


def test_calculate_visual_risk_single_uncorroborated_signal():
    """Verify single open-web match cannot trigger HIGH risk independently (capped at REVIEW)."""
    evidence = [
        {
            "signal_type": "external_image_reuse",
            "score": 88,
            "corroborated": False,
            "asset_evidence_level": "UNCORROBORATED_SINGLE_SOURCE",
        }
    ]
    score, level, action = calculate_visual_risk(evidence, brand_verification_status="UNAVAILABLE")
    assert score <= 60
    assert level == "REVIEW"
    assert action == "ADDITIONAL_VERIFICATION"


def test_calculate_visual_risk_corroborated_dual_signals():
    """Verify multiple corroborating vectors (reuse + verified logo mismatch) trigger HIGH risk."""
    evidence = [
        {
            "signal_type": "external_image_reuse",
            "score": 85,
            "corroborated": True,
            "asset_evidence_level": "CORROBORATED_POTENTIAL_REUSE",
        },
        {
            "signal_type": "potential_logo_mismatch",
            "score": 75,
        },
    ]
    score, level, action = calculate_visual_risk(evidence, brand_verification_status="VERIFIED")
    assert score >= 70
    assert level == "HIGH"
    assert action == "MANUAL_REVIEW"


def test_calculate_visual_risk_severe_tampering():
    """Verify high tampering/manipulation score independently triggers HIGH risk."""
    evidence = [
        {
            "signal_type": "manipulation",
            "score": 82,
        }
    ]
    score, level, action = calculate_visual_risk(evidence)
    assert score >= 70
    assert level == "HIGH"
    assert action == "MANUAL_REVIEW"


def test_calculate_visual_risk_clean_low():
    """Verify low scores result in LOW risk and NORMAL_FLOW."""
    evidence = [
        {
            "signal_type": "external_image_reuse",
            "score": 20,
        },
        {
            "signal_type": "manipulation",
            "score": 15,
        },
    ]
    score, level, action = calculate_visual_risk(evidence)
    assert score < 40
    assert level == "LOW"
    assert action == "NORMAL_FLOW"
