"""
visual_score.py — Visual Risk Scoring Engine.
Aggregates individual visual module signals into a unified,
calibrated Visual Risk Score (0-100) with documented weights.
"""

from __future__ import annotations

from typing import Dict, Any


# Configurable weights for each visual risk dimension
WEIGHTS = {
    "image_reuse": 0.30,         # 30% — Stolen / scraped catalog photos
    "logo_inconsistency": 0.20,   # 20% — Discrepancy with verified brand logo
    "manipulation": 0.25,         # 25% — ELA / splicing / editing indicators
    "synthetic_signal": 0.10,     # 10% — AI generation / diffusion indicators
    "identity_dispersion": 0.15,  # 15% — Cross-image visual identity coherence
}


def calculate_visual_risk_score(
    reuse_data: Dict[str, Any],
    logo_data: Dict[str, Any],
    manipulation_data: Dict[str, Any],
    cross_identity_coherence: float = 85.0,  # 0-100, where 100 is high internal consistency
) -> Dict[str, Any]:
    """
    Calculate composite Visual Risk Score from individual module outputs.

    Parameters
    ----------
    reuse_data : Output from analyze_multiple_images_reuse or analyze_image_reuse
    logo_data : Output from check_logo_consistency
    manipulation_data : Output from analyze_image_manipulation
    cross_identity_coherence : Score measuring how consistent the merchant's own visual style is

    Returns
    -------
    dict with breakdown, final visual_risk_score (0-100), risk_level, and audit trail
    """
    # 1. Image reuse risk (0-100)
    reuse_risk = float(reuse_data.get("reuse_risk_score", reuse_data.get("similarity", 0.0) * 100.0))

    # 2. Logo inconsistency risk (0-100)
    logo_inconsistency_risk = float(logo_data.get("inconsistency_risk", 0.0))

    # 3. Manipulation evidence score (0-100)
    manipulation_risk = float(manipulation_data.get("manipulation_score", 0.0))

    # 4. Synthetic signal suspicion (0-100)
    synthetic_risk = float(manipulation_data.get("synthetic_score", 10.0))

    # 5. Visual Identity Dispersion Risk (0-100) -> 100 - coherence
    identity_dispersion_risk = float(max(0.0, min(100.0, 100.0 - cross_identity_coherence)))

    # Weighted calculation
    composite_score = (
        WEIGHTS["image_reuse"] * reuse_risk
        + WEIGHTS["logo_inconsistency"] * logo_inconsistency_risk
        + WEIGHTS["manipulation"] * manipulation_risk
        + WEIGHTS["synthetic_signal"] * synthetic_risk
        + WEIGHTS["identity_dispersion"] * identity_dispersion_risk
    )

    visual_risk_score = round(float(max(0.0, min(100.0, composite_score))), 1)

    if visual_risk_score >= 70.0:
        risk_level = "HIGH"
    elif visual_risk_score >= 40.0:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "visual_risk_score": visual_risk_score,
        "risk_level": risk_level,
        "weights": WEIGHTS,
        "breakdown": {
            "image_reuse": {
                "score": round(reuse_risk, 1),
                "weight": WEIGHTS["image_reuse"],
                "weighted_contribution": round(reuse_risk * WEIGHTS["image_reuse"], 1),
                "label": "Image Reuse Risk",
            },
            "logo_inconsistency": {
                "score": round(logo_inconsistency_risk, 1),
                "weight": WEIGHTS["logo_inconsistency"],
                "weighted_contribution": round(logo_inconsistency_risk * WEIGHTS["logo_inconsistency"], 1),
                "label": "Logo Inconsistency",
            },
            "manipulation": {
                "score": round(manipulation_risk, 1),
                "weight": WEIGHTS["manipulation"],
                "weighted_contribution": round(manipulation_risk * WEIGHTS["manipulation"], 1),
                "label": "Manipulation Indicators",
            },
            "synthetic_signal": {
                "score": round(synthetic_risk, 1),
                "weight": WEIGHTS["synthetic_signal"],
                "weighted_contribution": round(synthetic_risk * WEIGHTS["synthetic_signal"], 1),
                "label": "Synthetic-Image Suspicion",
            },
            "identity_dispersion": {
                "score": round(identity_dispersion_risk, 1),
                "weight": WEIGHTS["identity_dispersion"],
                "weighted_contribution": round(identity_dispersion_risk * WEIGHTS["identity_dispersion"], 1),
                "label": "Visual Identity Dispersion",
            },
        },
    }
