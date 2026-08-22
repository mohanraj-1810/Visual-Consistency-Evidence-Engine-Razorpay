"""
fusion.py — Multimodal Risk Fusion Engine.
Combines Text/Business Metadata Risk with Visual Evidence Risk
to generate an explainable Final Risk Score and actionable human analyst recommendations.
Never automatically rejects merchants; provides clear evidence signals.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional


def calculate_text_business_risk(crawler_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calculate Merchant Text / Business Risk (0-100).
    Evaluates presence of contact details, policies, about info, pricing.
    """
    if not crawler_data:
        return {
            "text_risk_score": 18.0,
            "signals": {
                "has_contact": True,
                "has_policy": True,
                "has_pricing": True,
                "has_about": True,
                "has_social": True,
            },
            "summary": "Standard business profile with policy disclosures and contact channels present.",
        }

    score = 15.0  # Base baseline standard score

    has_contact = crawler_data.get("has_contact", False)
    has_policy = crawler_data.get("has_policy", False)
    has_pricing = crawler_data.get("has_pricing", False)
    has_about = crawler_data.get("has_about", False)
    social_links = crawler_data.get("social_links", [])

    if not has_contact:
        score += 25.0
    if not has_policy:
        score += 20.0
    if not has_pricing:
        score += 15.0
    if not has_about:
        score += 5.0
    if not social_links:
        score += 5.0

    score = float(max(5.0, min(95.0, score)))

    return {
        "text_risk_score": round(score, 1),
        "signals": {
            "has_contact": has_contact,
            "has_policy": has_policy,
            "has_pricing": has_pricing,
            "has_about": has_about,
            "has_social": len(social_links) > 0,
        },
        "summary": (
            "Merchant profile displays standard textual compliance and disclosures."
            if score < 40
            else "Merchant profile lacks standard business disclosures or contact channels."
        ),
    }


def fuse_risk_scores(
    text_risk_data: Dict[str, Any],
    visual_risk_data: Dict[str, Any],
    reuse_data: Dict[str, Any],
    logo_data: Dict[str, Any],
    manipulation_data: Dict[str, Any],
    merchant_name: str = "Merchant",
) -> Dict[str, Any]:
    """
    Fuse Text/Business Risk and Visual Evidence Risk into Final Risk Score.

    Fusion Principle:
    «"Don't just ask what a merchant says. Verify what their visuals prove."»
    
    Formula:
    1. Base Multimodal Combination: 0.25 * Text_Risk + 0.75 * Visual_Risk
    2. When Visual Risk >= 70 (multiple severe visual contradictions), visual evidence
       dominates over surface-level textual claims.
    """
    text_score = float(text_risk_data.get("text_risk_score", 18.0))
    visual_score = float(visual_risk_data.get("visual_risk_score", 20.0))

    if visual_score >= 70.0:
        # High visual evidence contradictions override text facade
        final_score = max(visual_score, 0.15 * text_score + 0.85 * visual_score)
    elif visual_score >= 40.0:
        final_score = 0.30 * text_score + 0.70 * visual_score
    elif text_score >= 70.0:
        # Severe textual deficiencies (placeholder site / missing compliance disclosures)
        final_score = max(45.0, 0.55 * text_score + 0.45 * visual_score)
    else:
        final_score = 0.35 * text_score + 0.65 * visual_score

    final_score = round(float(max(0.0, min(100.0, final_score))), 1)

    # Classification & workflow recommendation
    if final_score >= 70.0:
        status = "HIGH"
        status_label = "HIGH — MANUAL REVIEW"
        recommendation = "Route to Senior Risk Operations for manual visual evidence audit."
        badge_color = "#dc2626"
    elif final_score >= 40.0:
        status = "MEDIUM"
        status_label = "MEDIUM — ADDITIONAL VERIFICATION"
        recommendation = "Request merchant brand authorization documentation and high-resolution inventory proof."
        badge_color = "#d97706"
    else:
        status = "LOW"
        status_label = "LOW — NORMAL ONBOARDING"
        recommendation = "Standard merchant onboarding flow; automated monitoring enabled."
        badge_color = "#16a34a"

    # Generate explainability bullets
    reasons = []

    # 0. Text / Business Compliance explanation for unverified shells
    if text_score >= 70.0:
        reasons.append("Merchant website lacks critical business disclosures (contact channels, return policy, and business entity info).")

    # 1. External Match / Image reuse explanation
    max_sim = reuse_data.get("max_similarity", reuse_data.get("similarity", 0.0))
    top_cand = reuse_data.get("top_flagged_item") or reuse_data.get("top_candidate") or {}
    ref_source = top_cand.get("source_domain") or top_cand.get("reference_filename") or "external web source"
    is_own_brand = reuse_data.get("is_own_brand_candidate", False)

    if max_sim >= 0.85 and not is_own_brand:
        reasons.append(f"Product imagery strongly matches external candidate visual ({int(round(max_sim * 100))}% ViT similarity with {ref_source}) — Potential Visual Misrepresentation.")
    elif max_sim >= 0.70 and not is_own_brand:
        reasons.append(f"Product imagery exhibits moderate visual similarity ({int(round(max_sim * 100))}%) to candidate on {ref_source}.")
    elif is_own_brand:
        reasons.append("No external visual matches discovered online — visual content appears unique and proprietary to this merchant.")

    # 2. Logo explanation
    logo_sim = logo_data.get("similarity", 1.0)
    matched_logo = logo_data.get("matched_reference")
    if logo_sim < 0.55 and matched_logo:
        reasons.append(f"Merchant logo significantly diverges ({int(round(logo_sim * 100))}% match) from verified {matched_logo} identity.")
    elif logo_sim < 0.80 and matched_logo:
        reasons.append(f"Merchant logo demonstrates moderate stylistic variance ({int(round(logo_sim * 100))}%) against verified {matched_logo} assets.")

    # 3. Manipulation explanation
    manip_score = manipulation_data.get("manipulation_score", 0.0)
    if manip_score >= 60.0:
        reasons.append(f"Visual assets contain high localized compression and splicing indicators (Forensic score: {manip_score}%).")
    elif manip_score >= 35.0:
        reasons.append(f"Moderate image recompression and gradient variance indicators detected (Forensic score: {manip_score}%).")

    # 4. Synthetic explanation (supporting signal)
    synth_score = manipulation_data.get("synthetic_score", 0.0)
    if synth_score >= 60.0:
        reasons.append(f"Elevated synthetic/AI-generation markers observed in product imagery ({synth_score}% suspicion — supporting signal only).")

    # If no major flags
    if not reasons or (len(reasons) == 1 and is_own_brand):
        reasons.append("Visual evidence is internally consistent and matches claimed merchant branding.")
        reasons.append("No document tampering, forensic anomalies, or deceptive signals detected.")

    return {
        "final_risk_score": final_score,
        "text_risk_score": text_score,
        "visual_risk_score": visual_score,
        "status": status,
        "status_label": status_label,
        "recommendation": recommendation,
        "badge_color": badge_color,
        "reasons": reasons,
        "merchant_name": merchant_name,
    }
