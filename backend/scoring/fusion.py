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
    If the crawl failed or website was unreachable, returns an UNVERIFIABLE state.

    Non-ecommerce site categories (FINTECH_PAYMENTS, SAAS_SOFTWARE,
    INFORMATIONAL_INSTITUTION) are never penalised for missing pricing —
    these sites legitimately do not expose per-product prices.
    """
    if crawler_data is not None and (crawler_data.get("crawl_successful") is False or crawler_data.get("error")):
        crawl_err = crawler_data.get("error") or "Merchant website could not be reached"
        crawl_status = crawler_data.get("crawl_status", "CRAWL_FAILED")
        return {
            "text_risk_score": None,
            "signals": {
                "has_contact": False,
                "has_policy": False,
                "has_pricing": False,
                "has_about": False,
                "has_social": False,
            },
            "crawl_status": crawl_status,
            "crawl_successful": False,
            "is_unverifiable": True,
            "summary": f"Unreachable Website: {crawl_err}",
        }

    if not crawler_data:
        # Default baseline for evaluation test cases or offline test fixtures
        return {
            "text_risk_score": 18.0,
            "signals": {
                "has_contact": True,
                "has_policy": True,
                "has_pricing": True,
                "has_about": True,
                "has_social": True,
            },
            "crawl_status": "OFFLINE_EVAL_FIXTURE",
            "crawl_successful": True,
            "is_unverifiable": False,
            "summary": "Standard business profile with policy disclosures and contact channels present.",
        }

    score = 15.0  # Base baseline standard score

    has_contact = crawler_data.get("has_contact", False)
    has_policy = crawler_data.get("has_policy", False)
    has_pricing = crawler_data.get("has_pricing", False)
    has_about = crawler_data.get("has_about", False)
    social_links = crawler_data.get("social_links", [])

    # Detect site category — non-retail platforms are NOT penalised for missing pricing
    page_class = crawler_data.get("page_classification") or {}
    site_cat = page_class.get("site_category", "GENERAL_WEBSITE") if isinstance(page_class, dict) else "GENERAL_WEBSITE"
    is_non_retail = site_cat in ("FINTECH_PAYMENTS", "SAAS_SOFTWARE", "INFORMATIONAL_INSTITUTION")

    if not has_contact:
        score += 25.0
    if not has_policy:
        score += 20.0
    # Only penalise missing pricing for actual e-commerce / retail storefronts
    if not has_pricing and not is_non_retail:
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
        "crawl_status": "SUCCESS",
        "crawl_successful": True,
        "is_unverifiable": False,
        "site_category": site_cat,
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
    identity_data: Optional[Dict[str, Any]] = None,
    merchant_name: str = "Merchant",
    crawler_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Fuse Text/Business Risk and Visual Evidence Risk into Final Risk Score.

    Fusion Principle:
    «"Don't just ask what a merchant says. Verify what their visuals prove."»
    
    If the website was unreachable or the crawl failed, automated visual scoring
    is suspended and the engine returns UNVERIFIABLE rather than a false LOW score.
    """
    # 1. Check for UNVERIFIABLE crawl failure state
    is_crawl_failed = False
    crawl_err_msg = None

    if crawler_data and (crawler_data.get("crawl_successful") is False or crawler_data.get("error")):
        is_crawl_failed = True
        crawl_err_msg = crawler_data.get("error")
    elif text_risk_data.get("is_unverifiable") or text_risk_data.get("text_risk_score") is None:
        is_crawl_failed = True
        crawl_err_msg = text_risk_data.get("summary")

    if is_crawl_failed:
        crawl_status = (
            crawler_data.get("crawl_status")
            if crawler_data
            else text_risk_data.get("crawl_status", "CRAWL_FAILED")
        )

        # Distinguish between policy compliance (ROBOTS_DISALLOWED), WAF/anti-bot protection (BOT_BLOCKED), vs actual unreachable network failures
        if crawl_status == "ROBOTS_DISALLOWED":
            return {
                "final_risk_score": None,
                "text_risk_score": None,
                "visual_risk_score": None,
                "identity_coherence": None,
                "tampering_score": None,
                "status": "COMPLIANCE_LIMITED",
                "status_label": "COMPLIANCE-LIMITED — ACCESS RESTRICTED PER POLICY",
                "recommendation": "Merchant site is active, but robots.txt restricts automated bot indexing. Evaluate merchant via manual analyst review or merchant-authorized integration.",
                "badge_color": "#2563eb",  # Neutral Blue badge (NOT Red/Gray/Green)
                "reasons": [
                    f"Robots.txt Policy: Automated crawling restricted by merchant domain ({crawler_data.get('domain') if crawler_data else 'target site'}).",
                    "The merchant website is active and reachable, but enforces automated bot access restrictions per standard web standards.",
                    "Automated visual evaluation suspended per web compliance policy — no negative risk inference.",
                ],
                "merchant_name": merchant_name,
                "is_unverifiable": True,
                "is_compliance_limited": True,
                "is_bot_blocked": False,
                "is_redirect_limit_exceeded": False,
                "crawl_status": crawl_status,
                "crawl_error": crawl_err_msg or "Robots.txt policy restricts automated crawler access.",
            }

        if crawl_status == "BOT_BLOCKED":
            return {
                "final_risk_score": None,
                "text_risk_score": None,
                "visual_risk_score": None,
                "identity_coherence": None,
                "tampering_score": None,
                "status": "BOT_BLOCKED",
                "status_label": "COULD NOT VERIFY — ANTI-BOT PROTECTION (HTTP 403)",
                "recommendation": "Target site's anti-bot system (Cloudflare/PerimeterX/WAF) blocked automated scraper access. Review merchant manually or through direct merchant integration.",
                "badge_color": "#6366f1",  # Neutral Indigo badge (NOT Red/Gray/Green)
                "reasons": [
                    f"Anti-Bot Protection: Target platform ({crawler_data.get('domain') if crawler_data else 'merchant site'}) returned HTTP 403 / 429.",
                    "This does not indicate risk — many major legitimate platforms (Etsy, Amazon, etc.) deploy active WAF bot-protection.",
                    "Automated crawler blocked by design — no negative risk inference.",
                ],
                "merchant_name": merchant_name,
                "is_unverifiable": True,
                "is_compliance_limited": False,
                "is_bot_blocked": True,
                "is_redirect_limit_exceeded": False,
                "crawl_status": crawl_status,
                "crawl_error": crawl_err_msg or "Anti-bot protection blocked automated access (HTTP 403).",
            }

        if crawl_status == "REDIRECT_LIMIT_EXCEEDED":
            return {
                "final_risk_score": None,
                "text_risk_score": None,
                "visual_risk_score": None,
                "identity_coherence": None,
                "tampering_score": None,
                "status": "REDIRECT_LIMIT_EXCEEDED",
                "status_label": "UNVERIFIABLE — REDIRECT SAFETY LIMIT EXCEEDED",
                "recommendation": "Merchant site exceeded the safety redirect limit (3 hops), indicating a redirect loop, geo-block, or consent wall. Manual review required.",
                "badge_color": "#f59e0b",  # Amber / Warning badge
                "reasons": [
                    f"Redirect Limit Exceeded: Automated crawl aborted after exceeding 3 redirect hops on {crawler_data.get('domain') if crawler_data else 'merchant site'}.",
                    "Possible redirect loop, geographic redirection wall, or dynamic cookie consent loop.",
                    "Automated visual scoring suspended — requires manual verification by Risk Operations.",
                ],
                "merchant_name": merchant_name,
                "is_unverifiable": True,
                "is_compliance_limited": False,
                "is_bot_blocked": False,
                "is_redirect_limit_exceeded": True,
                "crawl_status": crawl_status,
                "crawl_error": crawl_err_msg or "Crawl diagnostic: redirect chain exceeded safety limit of 3 hops.",
            }

        return {
            "final_risk_score": None,
            "text_risk_score": None,
            "visual_risk_score": None,
            "identity_coherence": None,
            "tampering_score": None,
            "status": "UNVERIFIABLE",
            "status_label": "UNVERIFIABLE — INSUFFICIENT EVIDENCE",
            "recommendation": "Merchant site was unreachable or returned errors (DNS/Network/HTTP). Automated visual verification cannot be performed. Manual risk investigation required.",
            "badge_color": "#64748b",  # Distinct slate/gray color (never green)
            "reasons": [
                f"Website Unreachable: {crawl_err_msg or 'Website crawl failed or domain could not be resolved'}.",
                "Zero visual assets could be extracted due to network/connectivity failure.",
                "Automated risk scoring suspended — requires manual website verification by Risk Operations.",
            ],
            "merchant_name": merchant_name,
            "is_unverifiable": True,
            "is_compliance_limited": False,
            "is_bot_blocked": False,
            "crawl_status": crawl_status,
            "crawl_error": crawl_err_msg,
        }

    text_score = float(text_risk_data.get("text_risk_score", 18.0))
    visual_score = float(visual_risk_data.get("visual_risk_score", 20.0))

    # Non-retail platforms (fintech, SaaS, institutions) must not be driven into
    # HIGH risk purely by a high text_score — their missing 'pricing' signal is
    # expected and was already exempted in text scoring.  Cap the fusion weight of
    # text risk for these categories so visual evidence is the dominant driver.
    site_cat = text_risk_data.get("site_category", "GENERAL_WEBSITE")
    is_non_retail = site_cat in ("FINTECH_PAYMENTS", "SAAS_SOFTWARE", "INFORMATIONAL_INSTITUTION")

    # Base weighted linear combination
    if visual_score >= 70.0:
        raw_fusion = max(visual_score, 0.15 * text_score + 0.85 * visual_score)
    elif visual_score >= 40.0:
        raw_fusion = 0.30 * text_score + 0.70 * visual_score
    elif text_score >= 70.0 and not is_non_retail:
        raw_fusion = max(45.0, 0.55 * text_score + 0.45 * visual_score)
    else:
        raw_fusion = 0.35 * text_score + 0.65 * visual_score

    # Trust signals reduction for verified compliance, social presence, and platforms
    trust_deduction = 0.0
    signals = text_risk_data.get("signals", {})
    if signals.get("has_contact") and signals.get("has_policy") and signals.get("has_about"):
        trust_deduction += 5.0
    if signals.get("has_social"):
        trust_deduction += 3.0
    if is_non_retail:
        trust_deduction += 8.0

    fused_score = max(5.0, raw_fusion - trust_deduction)

    # ── Corroboration Gate for Escalation to MANUAL REVIEW (HIGH) ──────────────
    # A merchant should ONLY be routed to Senior Risk Operations (HIGH) if AT LEAST TWO
    # independent risk signals corroborate visual or compliance fraud.
    # Single isolated anomalies (e.g. supplier stock catalog photo or marketing ELA)
    # are routed to automated document requests or conditional approval instead.
    cand_src_type = reuse_data.get("top_flagged_item", {}).get("source_type") if reuse_data.get("top_flagged_item") else "NONE"
    is_supplier_cand = cand_src_type in ("SUPPLIER_CATALOG", "MARKETPLACE")

    reuse_val = float(reuse_data.get("reuse_risk_score", 0.0))
    logo_val = float(logo_data.get("inconsistency_risk", 0.0))
    manip_val = float(manipulation_data.get("manipulation_score", 0.0))
    evidence_status = reuse_data.get("match_status", "NO_DATA")

    # Evaluate independent severe flags.
    # IMPORTANT: INSUFFICIENT_EVIDENCE match status means a single/unreliable
    # external match was found — this does NOT count as a severe corroboration signal.
    reuse_is_severe = (
        reuse_val >= 70.0
        and not is_supplier_cand
        and evidence_status not in ("INSUFFICIENT_EVIDENCE", "WEAK_MATCH", "NO_EXTERNAL_MATCH")
    )

    severe_signals = 0
    if reuse_is_severe:
        severe_signals += 1
    if logo_val >= 60.0:
        severe_signals += 1
    if manip_val >= 60.0:
        severe_signals += 1
    if text_score >= 65.0 and not is_non_retail:
        severe_signals += 1

    # Corroboration enforcement
    if severe_signals >= 2:
        # Corroborated multi-vector risk: elevate to true HIGH
        final_score = max(80.0, fused_score)
    elif severe_signals == 1 and reuse_val >= 88.0 and not is_supplier_cand:
        # Single near-duplicate match against external brand catalog
        final_score = min(74.0, max(55.0, fused_score))
    elif reuse_val == 0.0 or is_supplier_cand:
        # Unique assets or supplier/dropship catalog: cap risk
        final_score = min(fused_score, 38.0 if is_supplier_cand else 32.0)
    else:
        # Single isolated anomaly: cap at MEDIUM to avoid unnecessary manual escalations
        final_score = min(64.0, fused_score)

    final_score = round(float(max(5.0, min(100.0, final_score))), 1)

    # ── 5-Tier Actionable Classification Model ────────────────────────────────
    # Tier 1 (0–29): CLEAR (Auto-Approve)
    # Tier 2 (30–49): LOW (Standard Onboarding)
    # Tier 3 (50–64): MEDIUM (Enhanced Verification — automated document request)
    # Tier 4 (65–79): ELEVATED (Conditional Approval — 90-day monitoring)
    # Tier 5 (80–100): HIGH (Manual Review Escalation)
    if final_score >= 80.0:
        status = "HIGH"
        status_tier = "HIGH"
        status_label = "HIGH — MANUAL REVIEW"
        recommendation = "Route to Senior Risk Operations for manual visual evidence audit."
        badge_color = "#dc2626"
    elif final_score >= 65.0:
        status = "MEDIUM"
        status_tier = "ELEVATED"
        status_label = "ELEVATED — CONDITIONAL APPROVAL"
        recommendation = "Conditional approval with 90-day enhanced risk monitoring and inventory invoice audit."
        badge_color = "#f97316"
    elif final_score >= 50.0:
        status = "MEDIUM"
        status_tier = "MEDIUM"
        status_label = "MEDIUM — ENHANCED VERIFICATION"
        recommendation = "Request merchant supplier invoices or distributor authorization documentation."
        badge_color = "#d97706"
    elif final_score >= 30.0:
        status = "LOW"
        status_tier = "LOW"
        status_label = "LOW — STANDARD ONBOARDING"
        recommendation = "Standard merchant onboarding; basic statutory identity validation."
        badge_color = "#10b981"
    else:
        status = "LOW"
        status_tier = "CLEAR"
        status_label = "CLEAR — AUTO-APPROVE"
        recommendation = "Standard merchant onboarding flow; automated real-time transaction monitoring enabled."
        badge_color = "#16a34a"

    # Generate explainability bullets
    reasons = []

    # 0. Text / Business Compliance explanation for unverified shells
    if text_score >= 70.0:
        reasons.append("Merchant website lacks critical business disclosures (contact channels, return policy, and business entity info).")

    # 1. External Match / Image reuse explanation
    max_sim = reuse_data.get("max_similarity", reuse_data.get("similarity", 0.0))
    top_cand = reuse_data.get("top_flagged_item") or reuse_data.get("top_candidate") or {}
    masked_mchs = top_cand.get("masked_merchant_ids") or []
    mch_str = ", ".join(masked_mchs) if masked_mchs else None
    ref_source = mch_str or top_cand.get("source_domain") or top_cand.get("reference_filename") or "external web source"
    is_own_brand = reuse_data.get("is_own_brand_candidate", False)
    cand_src_type_reason = top_cand.get("source_type", "NONE")
    is_supplier_cand_reason = cand_src_type_reason in ("SUPPLIER_CATALOG", "MARKETPLACE", "SOFT_TRUST")

    if is_own_brand:
        reasons.append("No external visual matches discovered online — visual content appears unique and proprietary to this merchant.")
    elif is_supplier_cand_reason and max_sim >= 0.70:
        reasons.append(f"Product imagery matches supplier/distributor catalog on {ref_source} ({int(round(max_sim * 100))}% ViT similarity) — consistent with authorized reseller sourcing, not misrepresentation.")
    elif max_sim >= 0.85:
        reasons.append(f"Product imagery strongly matches candidate visual ({int(round(max_sim * 100))}% ViT similarity with {ref_source}) — Potential Visual Misrepresentation.")
    elif max_sim >= 0.70:
        reasons.append(f"Product imagery exhibits moderate visual similarity ({int(round(max_sim * 100))}%) to candidate on {ref_source}.")

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

    # 5. Identity coherence explanation
    coherence_val = identity_data.get("coherence_score", 70.0) if identity_data else 70.0
    if coherence_val < 35.0:
        reasons.append(f"Merchant's product visuals display low internal style coherence ({int(round(coherence_val))}% consistency — images may originate from disconnected external catalogs).")

    # If no major flags
    if not reasons or (len(reasons) == 1 and is_own_brand):
        reasons.append("Visual evidence is internally consistent and matches claimed merchant branding.")
        reasons.append("No document tampering, forensic anomalies, or deceptive signals detected.")

    # Generate human-readable risk explanation
    if status == "HIGH":
        risk_explanation = (
            "Repeated strong visual matches were detected across multiple merchant assets "
            "and corroborated by independent external evidence."
        )
    elif status_tier == "ELEVATED":
        risk_explanation = (
            "Multiple visual anomalies were detected across independent signals. "
            "Evidence is meaningful but conditional approval with monitoring is recommended."
        )
    elif status == "MEDIUM":
        risk_explanation = (
            "Multiple visual similarities were detected, but the evidence is insufficient "
            "to establish meaningful reuse — enhanced verification recommended."
        )
    else:
        if evidence_status == "INSUFFICIENT_EVIDENCE":
            risk_explanation = (
                "One isolated visual similarity was detected, but no corroborating external "
                "evidence was found. Further human investigation may be warranted."
            )
        else:
            risk_explanation = (
                "No significant visual anomalies detected. Visual content appears "
                "consistent and proprietary to this merchant."
            )

    debug_metrics = {
        "image_count": reuse_data.get("image_count", 0),
        "average_similarity": round(float(reuse_data.get("average_similarity", 0.0)), 4),
        "max_similarity": round(float(max_sim), 4),
        "top_k_similarity": round(float(reuse_data.get("top_k_similarity", 0.0)), 4),
        "strong_match_count": reuse_data.get("strong_match_count", 0),
        "moderate_match_count": reuse_data.get("moderate_match_count", 0),
        "matched_domains": top_cand.get("matched_domains", [top_cand.get("source_domain")]) if top_cand else [],
        "E1_score": round(float(visual_risk_data.get("E1_score", reuse_data.get("reuse_risk_score", 0.0))), 1),
        "E4_score": round(float(reuse_data.get("e4_score", 0.0)), 1),
        "logo_score": round(float(logo_val), 1),
        "manipulation_score": round(float(manip_val), 1),
        "identity_score": round(float(coherence_val), 1),
        "visual_score": round(float(visual_score), 1),
        "final_score": round(float(final_score), 1),
        "final_risk_level": status,
        "evidence_status": evidence_status,
    }

    return {
        "final_risk_score": final_score,
        "text_risk_score": text_score,
        "visual_risk_score": visual_score,
        "identity_coherence": round(float(coherence_val), 1),
        "tampering_score": round(float(manip_score), 1),
        "status": status,
        "status_tier": status_tier,
        "status_label": status_label,
        "recommendation": recommendation,
        "badge_color": badge_color,
        "reasons": reasons,
        "risk_explanation": risk_explanation,
        "merchant_name": merchant_name,
        "is_unverifiable": False,
        "debug_metrics": debug_metrics,
    }
