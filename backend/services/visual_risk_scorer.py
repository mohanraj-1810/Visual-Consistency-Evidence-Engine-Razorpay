"""
services/visual_risk_scorer.py — Visual Risk Scoring and Multi-Signal Corroboration Engine.
Enforces all evidence safety rules:
- Google Vision open-web match alone or Local ViT match alone cannot cause HIGH risk.
- Corroborated potential visual reuse + another corroborating vector triggers HIGH risk.
- Strong document tampering/manipulation triggers HIGH risk.
- Maps risk levels safely: LOW -> NORMAL_FLOW, REVIEW -> ADDITIONAL_VERIFICATION, HIGH -> MANUAL_REVIEW.
- Never automatically rejects or labels a merchant as fraudulent.
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple


def calculate_visual_risk(
    evidence_list: List[Dict[str, Any]],
    brand_verification_status: str = "UNAVAILABLE",
) -> Tuple[int, str, str]:
    """
    Computes overall visual risk score and applies strict corroboration safety rules.

    Returns
    -------
    (visual_risk_score, risk_level, recommended_action)
    """
    if not evidence_list:
        return 0, "LOW", "NORMAL_FLOW"

    # Extract individual signal categories
    reuse_items = [e for e in evidence_list if e.get("signal_type") in ("external_image_reuse", "cross_merchant_visual_similarity")]
    logo_items = [e for e in evidence_list if e.get("signal_type") == "potential_logo_mismatch"]
    manip_items = [e for e in evidence_list if e.get("signal_type") == "manipulation"]

    # 1. Reuse / Cross-merchant Signals
    max_reuse_score = max([e.get("score", 0) for e in reuse_items], default=0)
    has_corroborated_reuse = any(e.get("corroborated", False) or e.get("asset_evidence_level") == "CORROBORATED_POTENTIAL_REUSE" for e in reuse_items)
    is_marketplace_only = all(e.get("is_marketplace_only", False) or e.get("is_stock_only", False) for e in reuse_items) if reuse_items else False
    
    # 2. Logo Mismatch Signal
    max_logo_score = 0
    if brand_verification_status == "VERIFIED" and logo_items:
        max_logo_score = max([e.get("score", 0) for e in logo_items], default=0)

    # 3. Manipulation / Tampering Signal
    max_manip_score = max([e.get("score", 0) for e in manip_items], default=0)

    # Identify active vectors
    active_scores = []
    has_reuse_vector = max_reuse_score >= 40
    has_logo_vector = max_logo_score >= 40
    has_manip_vector = max_manip_score >= 40

    if max_reuse_score > 0:
        active_scores.append(max_reuse_score)
    if max_logo_score > 0:
        active_scores.append(max_logo_score)
    if max_manip_score > 0:
        active_scores.append(max_manip_score)

    corroborating_signals_count = sum([has_reuse_vector, has_logo_vector, has_manip_vector])

    if not active_scores:
        return 0, "LOW", "NORMAL_FLOW"

    peak_score = max(active_scores)
    avg_active = sum(active_scores) / len(active_scores)

    # ── Multi-Signal Fusion Rules ──
    if corroborating_signals_count >= 2:
        # Multiple corroborating vectors (e.g. reuse + logo mismatch, or reuse + manipulation)
        base_score = 0.60 * peak_score + 0.40 * avg_active
    elif max_manip_score >= 70:
        # High individual tampering anomaly on certificates or statutory documents
        base_score = max_manip_score
    elif has_corroborated_reuse and peak_score >= 75 and corroborating_signals_count >= 2:
        # Corroborated dual-source visual reuse combined with another signal
        base_score = peak_score
    elif is_marketplace_only and corroborating_signals_count < 2:
        # Single isolated marketplace match
        base_score = min(55.0, peak_score * 0.85)
    else:
        # Single uncorroborated open-web or local-ViT signal is capped at REVIEW
        base_score = min(60.0, peak_score)

    final_score = int(round(max(0.0, min(100.0, base_score))))

    # ── Categorization & Action Recommendation ──
    if final_score >= 70:
        risk_level = "HIGH"
        recommended_action = "MANUAL_REVIEW"
    elif final_score >= 40:
        risk_level = "REVIEW"
        recommended_action = "ADDITIONAL_VERIFICATION"
    else:
        risk_level = "LOW"
        recommended_action = "NORMAL_FLOW"

    return final_score, risk_level, recommended_action
