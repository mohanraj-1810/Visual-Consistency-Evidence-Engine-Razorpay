"""
fusion.py — Multimodal Risk Fusion Engine.
Combines Simulated Existing Merchant Risk (Text/Business metadata)
with Visual Evidence Risk to generate an explainable Final Risk Score
and actionable analyst recommendations. Never rejects merchants automatically.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional


def calculate_text_business_risk(crawler_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calculate simulated business & text metadata risk score (0-100).
    Evaluates presence of contact details, policies, about info, pricing.
    """
    if not crawler_data:
        # Default baseline low risk for clean merchant demo
        return {
            "text_risk_score": 18.0,
            "signals": {
                "has_contact": True,
                "has_policy": True,
                "has_pricing": True,
                "has_about": True,
                "has_social": True,
            },
            "summary": "Standard business profile with policy pages and contact information present.",
        }

    score = 15.0  # Base standard score

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
        score += 10.0
    if not social_links:
        score += 10.0

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
    Fuse Text Risk and Visual Evidence Risk into Final Risk Score.

    Fusion Principle:
    «"Don't just ask what a merchant says. Verify what their visuals prove."»
    
    Formula:
    1. Base Linear Combination: 0.35 * Text_Risk + 0.65 * Visual_Risk
    2. Deceptive Visual Contrast Multiplier:
       If Visual Evidence Risk is elevated (Visual Risk >= 65) while Text Risk is low (< 40),
       the visual contradictions override surface-level text disclosures:
       Final_Risk = max(Visual_Risk, Visual_Risk + 0.08 * (100 - Text_Risk) * (Visual_Risk / 100))
    """
    text_score = float(text_risk_data.get("text_risk_score", 18.0))
    visual_score = float(visual_risk_data.get("visual_risk_score", 20.0))

    # Fusion Calculation
    if visual_score >= 65.0:
        if text_score < 40.0:
            # Deceptive contrast: legitimate-looking facade with contradictory visual evidence
            final_score = visual_score + 0.08 * (100.0 - text_score) * (visual_score / 100.0)
        else:
            final_score = 0.25 * text_score + 0.75 * visual_score
    elif visual_score >= 40.0:
        final_score = 0.30 * text_score + 0.70 * visual_score
    else:
        final_score = 0.35 * text_score + 0.65 * visual_score

    final_score = round(float(max(0.0, min(100.0, final_score))), 1)

    # Classification & workflow recommendation
    if final_score >= 70.0:
        status = "HIGH"
        status_label = "HIGH - MANUAL REVIEW"
        recommendation = "Route to Senior Risk Operations for manual visual evidence audit."
        badge_color = "#dc2626"
    elif final_score >= 40.0:
        status = "MEDIUM"
        status_label = "MEDIUM - ADDITIONAL VERIFICATION"
        recommendation = "Request merchant brand authorization letters and high-res inventory proof."
        badge_color = "#d97706"
    else:
        status = "LOW"
        status_label = "LOW - NORMAL FLOW"
        recommendation = "Standard merchant onboarding flow; automated monitoring enabled."
        badge_color = "#16a34a"

    # Generate explainability bullets ("WHY IS THIS MERCHANT HIGH / MEDIUM / LOW RISK?")
    reasons = []

    # 1. Reuse explanation
    max_sim = reuse_data.get("max_similarity", reuse_data.get("similarity", 0.0))
    ref_fname = reuse_data.get("top_flagged_item", {}).get("reference_filename") or reuse_data.get("reference_filename")
    if max_sim >= 0.85:
        reasons.append(f"Product imagery strongly matches existing catalog reference ({int(round(max_sim * 100))}% similarity with {ref_fname or 'reference asset'}).")
    elif max_sim >= 0.70:
        reasons.append(f"Product visuals exhibit moderate similarity ({int(round(max_sim * 100))}%) to catalog reference {ref_fname or 'database'}.")

    # 2. Logo explanation
    logo_sim = logo_data.get("similarity", 1.0)
    matched_logo = logo_data.get("matched_reference")
    if logo_sim < 0.55 and matched_logo:
        reasons.append(f"Merchant logo significantly diverges from verified visual identity for {matched_logo}.")
    elif logo_sim < 0.80 and matched_logo:
        reasons.append(f"Merchant logo demonstrates moderate stylistic variance against verified {matched_logo} brand assets.")

    # 3. Manipulation explanation
    manip_score = manipulation_data.get("manipulation_score", 0.0)
    if manip_score >= 60.0:
        reasons.append(f"Document / product visuals contain high localized compression and splicing indicators (Forensic score: {manip_score}%).")
    elif manip_score >= 35.0:
        reasons.append(f"Minor image recompression and gradient variance indicators detected (Forensic score: {manip_score}%).")

    # 4. Synthetic explanation
    synth_score = manipulation_data.get("synthetic_score", 0.0)
    if synth_score >= 60.0:
        reasons.append(f"Elevated synthetic/AI-generation markers observed in product imagery ({synth_score}% suspicion).")

    # If no major flags
    if not reasons:
        reasons.append("Visual evidence is consistent across products and matches claimed merchant branding.")
        reasons.append("No visual reuse, document tampering, or forensic anomalies detected.")

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
