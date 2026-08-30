"""
visual_score.py — Visual Risk Scoring Engine.
Aggregates individual visual module signals into a calibrated Visual Risk Score (0-100)
using weighted baseline metrics and multi-signal corroboration.

E1 (Local Reference Reuse) and E4 (Serper External Evidence) are computed independently
and kept separate throughout scoring. Neither alone can produce HIGH risk.
"""

from __future__ import annotations

from typing import Dict, Any, List
import numpy as np


# Calibrated baseline weights for visual risk dimensions
WEIGHTS = {
    "image_reuse": 0.40,         # 40% — Stolen / scraped catalog photos (strongest signal)
    "logo_inconsistency": 0.15,   # 15% — Discrepancy with verified brand logo
    "manipulation": 0.25,         # 25% — ELA / splicing / editing indicators
    "synthetic_signal": 0.08,     # 8%  — AI generation / diffusion indicators
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

    E1/E4 Separation Principle:
    - E1_score is derived exclusively from local reference-dataset reuse signals.
    - E4_score is derived exclusively from Serper external candidate evidence
      (verify_candidates_with_vit output, 'e4_score' field).
    - These are NEVER cross-contaminated.

    Corroboration Principle:
    - A single isolated anomaly (E1 alone, E4 alone, manipulation alone)
      CANNOT independently produce HIGH visual risk.
    - HIGH visual risk requires 2+ independent severe signals.

    Own-Brand Principle:
    - When no external/reference matches exist, reuse risk = 0.
    """
    match_status = reuse_data.get("match_status", "")
    is_own_brand = reuse_data.get("is_own_brand_candidate", False)

    # ── E1: Local/Reference Reuse Signal ─────────────────────────────────────
    # Derived ONLY from local reference dataset comparisons (image_reuse.py).
    # Never populated from Serper/external search results.
    if is_own_brand or match_status in ("NO_EXTERNAL_MATCH", ""):
        E1_score = 0.0
    elif match_status == "INSUFFICIENT_EVIDENCE":
        raw_e1 = float(reuse_data.get("reuse_risk_score", 0.0))
        E1_score = min(35.0, raw_e1)
    elif match_status == "WEAK_MATCH":
        raw_e1 = float(reuse_data.get("reuse_risk_score", 0.0))
        E1_score = min(25.0, raw_e1)
    else:
        # CORROBORATED_EXTERNAL_MATCH or legacy local fixture (unlabelled)
        E1_score = float(reuse_data.get("reuse_risk_score", 0.0))

    # ── E4: Serper External Evidence Signal ───────────────────────────────────
    # Derived ONLY from verify_candidates_with_vit output ('e4_score' field).
    # Already calibrated: INSUFFICIENT_EVIDENCE<=35, soft-trust-only<=20, CORROBORATED<=80.
    E4_score = float(reuse_data.get("e4_score", 0.0))

    # Combined reuse risk = max(E1, E4) — avoids double-counting while surfacing dominant signal
    reuse_risk = max(E1_score, E4_score)

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

    # ── Multi-Signal Corroboration Engine ──────────────────────────────────────
    # Only amplify when 2+ independent primary signals are severe (>=65).
    # A single severe signal does NOT get amplified — fusion enforces that gate.
    primary_signals = [reuse_risk, logo_inconsistency_risk, manipulation_risk]
    severe_flags = [s for s in primary_signals if s >= 65.0]
    moderate_flags = [s for s in primary_signals if s >= 40.0]

    if len(severe_flags) >= 2:
        corroborated_score = 0.55 * max(primary_signals) + 0.35 * sorted(primary_signals, reverse=True)[1] + 0.10 * linear_base
        composite_score = max(linear_base, corroborated_score)
    elif len(severe_flags) == 1 and len(moderate_flags) >= 2:
        corroborated_score = 0.45 * max(primary_signals) + 0.30 * sorted(primary_signals, reverse=True)[1] + 0.25 * linear_base
        composite_score = max(linear_base, corroborated_score)
    else:
        # Single signal or no severe flags: no amplification
        composite_score = linear_base

    # Guard: if no reuse evidence AND no meaningful logo anomaly, cap at LOW.
    if reuse_risk == 0.0 and logo_inconsistency_risk < 50.0:
        composite_score = min(composite_score, 38.0)
    elif reuse_risk == 0.0 and manipulation_risk < 35.0 and logo_inconsistency_risk < 50.0:
        composite_score = min(composite_score, 28.0)

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
        "E1_score": round(E1_score, 1),
        "E4_score": round(E4_score, 1),
        "breakdown": {
            "E1_local_reuse": {
                "score": round(E1_score, 1),
                "label": "E1 — Local Reference Reuse",
                "note": "Local/reference dataset similarity evidence only",
            },
            "E4_external_evidence": {
                "score": round(E4_score, 1),
                "label": "E4 — Serper External Evidence",
                "note": "Calibrated score from external candidate verification (not raw ViT similarity)",
            },
            "image_reuse": {
                "score": round(reuse_risk, 1),
                "weight": WEIGHTS["image_reuse"],
                "weighted_contribution": round(reuse_risk * WEIGHTS["image_reuse"], 1),
                "label": "Image Reuse Risk (max of E1, E4)",
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

