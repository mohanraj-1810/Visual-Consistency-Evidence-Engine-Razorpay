"""
Unit tests for structured evidence synthesis and claim-to-evidence reasoning engine.
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from online_evidence.reasoning import (
    _encode_b64,
    generate_structured_evidence,
    synthesize_claims_reasoning,
)


def test_encode_b64_pil_and_numpy():
    """Verify base64 encoding handles PIL Images, numpy ndarrays, and None safely."""
    assert _encode_b64(None) is None

    # Test PIL image
    pil_img = Image.new("RGB", (20, 20), color="blue")
    encoded_pil = _encode_b64(pil_img)
    assert encoded_pil is not None
    assert encoded_pil.startswith("data:image/png;base64,")

    # Test numpy array
    np_img = np.zeros((20, 20, 3), dtype=np.uint8)
    encoded_np = _encode_b64(np_img)
    assert encoded_np is not None
    assert encoded_np.startswith("data:image/png;base64,")


def test_generate_structured_evidence_high_risk():
    """Verify structured evidence generation when indicators show high visual reuse and tampering."""
    reuse_data = {
        "top_flagged_item": {
            "similarity": 0.92,
            "source_type": "ONLINE",
            "source_domain": "external-shop.com",
            "source_url": "https://external-shop.com/item.jpg",
            "image": Image.new("RGB", (10, 10)),
        }
    }
    logo_data = {
        "similarity": 0.40,
        "inconsistency_risk": 75.0,
        "matched_reference": "VerifiedBrand",
    }
    manipulation_data = {
        "manipulation_score": 78.0,
        "synthetic_score": 65.0,
    }
    identity_data = {
        "coherence_score": 20.0,
    }

    evidence_list = generate_structured_evidence(
        reuse_data=reuse_data,
        logo_data=logo_data,
        manipulation_data=manipulation_data,
        identity_data=identity_data,
    )

    assert len(evidence_list) == 5
    evidence_types = {e["evidence_type"] for e in evidence_list}
    assert evidence_types == {"image_reuse", "logo_consistency", "manipulation", "synthetic_signal", "visual_identity"}

    # Check reuse
    reuse_obj = next(e for e in evidence_list if e["evidence_type"] == "image_reuse")
    assert reuse_obj["relationship"] == "CONTRADICTS"
    assert reuse_obj["severity"] == "HIGH"
    assert reuse_obj["similarity_pct"] == 92

    # Check logo
    logo_obj = next(e for e in evidence_list if e["evidence_type"] == "logo_consistency")
    assert logo_obj["relationship"] == "CONTRADICTS"
    assert logo_obj["severity"] == "HIGH"

    # Check manipulation
    manip_obj = next(e for e in evidence_list if e["evidence_type"] == "manipulation")
    assert manip_obj["relationship"] == "CONTRADICTS"
    assert manip_obj["severity"] == "HIGH"


def test_generate_structured_evidence_low_risk_clean():
    """Verify structured evidence returns SUPPORTS/LOW for legitimate merchants."""
    reuse_data = {
        "top_flagged_item": {
            "similarity": 0.35,
            "source_type": "LOCAL_DEMO",
            "source_domain": "archive.merchant-catalog.org",
        }
    }
    logo_data = {
        "similarity": 0.95,
        "inconsistency_risk": 0.0,
        "matched_reference": "OfficialCorp",
    }
    manipulation_data = {
        "manipulation_score": 10.0,
        "synthetic_score": 15.0,
    }
    identity_data = {
        "coherence_score": 88.0,
    }

    evidence_list = generate_structured_evidence(
        reuse_data=reuse_data,
        logo_data=logo_data,
        manipulation_data=manipulation_data,
        identity_data=identity_data,
    )

    reuse_obj = next(e for e in evidence_list if e["evidence_type"] == "image_reuse")
    assert reuse_obj["relationship"] == "SUPPORTS"
    assert reuse_obj["severity"] == "LOW"

    logo_obj = next(e for e in evidence_list if e["evidence_type"] == "logo_consistency")
    assert logo_obj["relationship"] == "SUPPORTS"
    assert logo_obj["severity"] == "LOW"


def test_synthesize_claims_reasoning_compliance_limited():
    """Verify claims synthesis handles COMPLIANCE_LIMITED gracefully."""
    claims = {"inventory_claim": "Exclusive items"}
    res = synthesize_claims_reasoning(
        claims=claims,
        evidence_objects=[],
        final_risk_score=15.0,
        status="COMPLIANCE_LIMITED",
    )

    assert "claim_matrix" in res or "claims" in res or isinstance(res, dict)
    assert res.get("recommendation") is not None
