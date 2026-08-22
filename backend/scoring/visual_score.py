"""
visual_score.py — Visual Risk Scoring Engine.
Aggregates individual visual module signals into a calibrated Visual Risk Score (0-100)
using weighted baseline metrics and multi-signal corroboration.
Correctly handles own-brand unique visuals without falsely penalizing them.
"""

from __future__ import annotations

from typing import Dict, Any, List
import numpy as np


# Calibrated baseline weights for visual risk dimensions
WEIGHTS = {
    "image_reuse": 0.40,         # 40% — Stolen / scraped catalog photos (strongest signal)
    "logo_inconsistency": 0.15,   # 15% — Discrepancy with verified brand logo
    "manipulation": 0.25,         # 25% — ELA / splicing / editing indicators
    "synthetic_signal": 0.08,     # 8% — AI generation / diffusion indicators
    "identity_dispersion": 0.12,  # 12% — Cross-image visual identity coherence
}


def calculate_visual_risk_score(
    reuse_data: Dict[str, Any],
    logo_data: Dict[str, Any],
    manipulation_data: Dict[str, Any],
    cross_identity_coherence: float = 85.0,  # 0-100, where 100 is high internal consistency
) -> Dict[str, Any]:
    """
    Calculate composite Visual Risk Score from individual module outputs.

    Uses Multi-Signal Corroboration:
    When multiple independent visual dimensions (reuse, logo, manipulation)
    exhibit elevated risk, the corroborating evidence reinforces risk level,
    preventing linear dilution from misclassifying high-risk merchants as medium.

    Own-Brand Principle:
    When no external candidate matches exist (own-brand / unique products),
    reuse_risk is 0, ensuring original merchant products are never penalized.

    Parameters
    ----------
    reuse_data : Output from analyze_multiple_images_reuse, verifier, or analyze_image_reuse
    logo_data : Output from check_logo_consistency
    manipulation_data : Output from analyze_image_manipulation
    cross_identity_coherence : Score measuring internal visual catalog consistency

    Returns
    -------
    dict with breakdown, final visual_risk_score (0-100), risk_level, and audit trail
    """
    # 1. Image reuse risk (0-100)
    # If no external match is found or marked as own-brand, reuse risk is 0
    if reuse_data.get("is_own_brand_candidate", False) or reuse_data.get("match_status") == "NO_EXTERNAL_MATCH":
        reuse_risk = 0.0
    else:
        reuse_risk = float(reuse_data.get("reuse_risk_score", reuse_data.get("similarity", 0.0) * 100.0))

    # 2. Logo inconsistency risk (0-100)
    logo_inconsistency_risk = float(logo_data.get("inconsistency_risk", 0.0))

    # 3. Manipulation evidence score (0-100)
    manipulation_risk = float(manipulation_data.get("manipulation_score", 0.0))

    # 4. Synthetic signal suspicion (0-100)
    synthetic_risk = float(manipulation_data.get("synthetic_score", 10.0))

    # 5. Visual Identity Dispersion Risk (0-100) -> 100 - coherence
    identity_dispersion_risk = float(max(0.0, min(100.0, 100.0 - cross_identity_coherence)))

    # Base weighted linear combination
    linear_base = (
        WEIGHTS["image_reuse"] * reuse_risk
        + WEIGHTS["logo_inconsistency"] * logo_inconsistency_risk
        + WEIGHTS["manipulation"] * manipulation_risk
        + WEIGHTS["synthetic_signal"] * synthetic_risk
        + WEIGHTS["identity_dispersion"] * identity_dispersion_risk
    )

    # ── Multi-Signal Corroboration Engine ─────────────────────────────────────
    # Evaluate severe (>65) and moderate (>40) independent flags
    primary_signals = [reuse_risk, logo_inconsistency_risk, manipulation_risk]
    severe_flags = [s for s in primary_signals if s >= 65.0]
    moderate_flags = [s for s in primary_signals if s >= 40.0]

    # If 2 or more independent visual signals are severe (e.g. reuse + logo or reuse + manipulation),
    # corroboration ensures the risk reflects multiple independent contradictions
    if len(severe_flags) >= 2:
        # Corroborated high risk: top signals dominate
        corroborated_score = 0.55 * max(primary_signals) + 0.35 * sorted(primary_signals, reverse=True)[1] + 0.10 * linear_base
        composite_score = max(linear_base, corroborated_score)
    elif len(severe_flags) == 1 and len(moderate_flags) >= 2:
        corroborated_score = 0.45 * max(primary_signals) + 0.30 * sorted(primary_signals, reverse=True)[1] + 0.25 * linear_base
        composite_score = max(linear_base, corroborated_score)
    elif len(severe_flags) == 1 and max(primary_signals) >= 80.0:
        # Single very severe signal (e.g. 94% external image match)
        composite_score = max(linear_base, 0.65 * max(primary_signals) + 0.35 * linear_base)
    else:
        composite_score = linear_base

    # Guard: if reuse_risk is 0 and manipulation is low, cap visual risk to prevent false HIGH
    if reuse_risk == 0.0 and manipulation_risk < 35.0 and logo_inconsistency_risk < 50.0:
        composite_score = min(composite_score, 38.0)

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
        "corroboration_active": len(severe_flags) >= 2,
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
