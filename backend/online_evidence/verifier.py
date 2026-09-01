"""
verifier.py -- ViT-based Visual Similarity Verification for Candidate Evidence.
Verifies candidate online images using Vision Transformer (ViT) embeddings
and cosine similarity. Never blindly trusts search results alone.

Distinguishes:
  NO_EXTERNAL_MATCH         -- no meaningful external similarity found
  WEAK_MATCH                -- low-confidence similarity (0.55-0.69)
  INSUFFICIENT_EVIDENCE     -- similarity exists but single/unreliable source; cannot conclude reuse
  CORROBORATED_EXTERNAL_MATCH -- multiple strong matches from meaningful independent domains

E4 Evidence Principle:
  Serper finding a visually similar image does NOT prove image theft or fraud.
  ViT cosine similarity is a visual evidence signal only, not a fraud probability.
  A single high-similarity match on Pinterest/marketplace/stock CANNOT produce HIGH risk.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from PIL import Image
import numpy as np

from visual.vit_embeddings import get_image_embedding, compute_cosine_similarity


# Image aggregators, social media image boards, and stock-like platforms.
_IMAGE_AGGREGATORS = {
    "pinterest.com", "pinimg.com",
    "imgur.com",
    "googleusercontent.com", "ggpht.com",
    "wikimedia.org", "wikipedia.org",
    "staticflickr.com", "flickr.com",
    "instagram.com", "cdninstagram.com",
    "tumblr.com",
    "reddit.com", "redd.it",
}

# Marketplace/supplier/stock domains -- standard commercial distribution channels.
_SOFT_TRUST_DOMAINS = {
    "amazon.com", "amazon.in", "flipkart.com", "aliexpress.com", "ebay.com",
    "walmart.com", "alibaba.com", "etsy.com", "myntra.com", "ajio.com",
    "target.com", "shopee.com", "lazada.com", "temu.com", "shein.com",
    "dhgate.com", "made-in-china.com", "indiamart.com", "tradeindia.com",
    "globalsources.com", "chinabrands.com", "wholesale7.net",
    "shutterstock.com", "gettyimages.com", "freepik.com", "istockphoto.com",
    "unsplash.com", "pexels.com", "stock.adobe.com", "pixabay.com", "dreamstime.com",
    "catalog-archive.internal", "archive.merchant-catalog.org", "merchant-catalog.org",
    "supplier-catalog.internal", "supplier-catalog.org",
}


def _is_soft_trust_domain(domain: str) -> bool:
    """Return True if domain is a marketplace, stock site, image aggregator, or supplier catalog."""
    if not domain:
        return False
    from services.evidence_normalizer import _clean_domain_str, is_supplier_domain
    clean = _clean_domain_str(domain)
    return (
        any(clean == d or clean.endswith("." + d) for d in _SOFT_TRUST_DOMAINS)
        or any(clean == d or clean.endswith("." + d) for d in _IMAGE_AGGREGATORS)
        or is_supplier_domain(clean)
    )


@dataclass
class CandidateMatch:
    candidate_id: str
    similarity: float
    similarity_pct: int
    severity: str
    source_type: str
    source_url: str
    source_domain: str
    title: str
    image: Optional[Image.Image]
    explanation: str
    evidence_strength: str
    match_label: str


def verify_candidates_with_vit(
    merchant_image: Union[Image.Image, np.ndarray, str],
    candidates: List[Dict[str, Any]],
    high_threshold: float = 0.85,
    medium_threshold: float = 0.70,
    weak_threshold: float = 0.55,
    merchant_domain: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Passes discovered online candidates through our ViT similarity verifier.

    E4 Evidence Status Taxonomy
    ---------------------------
    NO_EXTERNAL_MATCH           : max external similarity < 0.55
    WEAK_MATCH                  : max external similarity 0.55-0.69
    INSUFFICIENT_EVIDENCE       : similarity >= 0.70 but insufficient corroboration
                                  (single match, soft-trust only, or no repeated domain pattern)
    CORROBORATED_EXTERNAL_MATCH : >= 2 strong meaningful matches, OR 1 strong + 1 moderate
                                  from non-soft-trust independent domains

    CRITICAL: A single match on Pinterest/marketplace/stock regardless of similarity magnitude
    MUST return INSUFFICIENT_EVIDENCE, NOT drive HIGH risk.
    """
    _empty = {
        "top_candidate": None,
        "all_candidates": [],
        "max_similarity": 0.0,
        "evidence_strength": "LOW",
        "match_status": "NO_EXTERNAL_MATCH",
        "is_own_brand_candidate": True,
        "source_type": "NONE",
        "strong_match_count": 0,
        "moderate_match_count": 0,
        "e4_score": 0.0,
    }

    if not candidates:
        return {**_empty, "explanation": "No external visual matches discovered online. Visual content appears unique / proprietary to the merchant."}

    try:
        merchant_emb = get_image_embedding(merchant_image)
    except Exception as e:
        return {**_empty, "explanation": f"ViT feature extraction notice: {str(e)}"}

    verified_list: List[Dict[str, Any]] = []
    clean_merchant_domain = merchant_domain.lower().replace("www.", "").strip() if merchant_domain else None

    for c in candidates:
        cand_img = c.get("image")
        if cand_img is None:
            continue

        try:
            cand_emb = get_image_embedding(cand_img)
            sim = float(compute_cosine_similarity(merchant_emb, cand_emb))
        except Exception:
            continue

        sim_pct = int(round(sim * 100))
        source_type = c.get("source_type", "ONLINE")
        source_domain = c.get("source_domain", "public-web-source.com").lower()
        source_url = c.get("source_url", "")
        title = c.get("title", f"Candidate {source_domain}")

        is_self_domain = False
        if clean_merchant_domain and (
            clean_merchant_domain in source_domain
            or source_domain in clean_merchant_domain
            or clean_merchant_domain.split(".")[0] in source_domain.split(".")[0]
        ):
            is_self_domain = True

        from services.evidence_normalizer import is_supplier_domain, is_marketplace_domain
        is_supplier = is_supplier_domain(source_domain)
        is_soft = _is_soft_trust_domain(source_domain)

        if is_self_domain:
            severity = "LOW"
            evidence_strength = "LOW"
            source_type = "OWN_DOMAIN"
            match_label = "Own Domain / Brand Verified"
            explanation = f"Verified merchant's own domain asset on {source_domain} ({sim_pct}% match)."

        elif is_supplier:
            severity = "LOW"
            evidence_strength = "LOW"
            source_type = "SUPPLIER_CATALOG"
            match_label = "Supplier / Manufacturer Catalog Asset"
            explanation = (
                f"Product imagery matches supplier catalog on {source_domain} ({sim_pct}% match). "
                "Common for resellers and distributors — does not indicate visual fraud."
            )

        elif is_soft:
            severity = "LOW" if sim < high_threshold else "MEDIUM"
            evidence_strength = "LOW"
            source_type = "SOFT_TRUST"
            match_label = "Image Aggregator / Marketplace Match"
            explanation = (
                f"Visual match on {source_domain} ({sim_pct}% similarity). "
                "This source (marketplace/aggregator/stock) commonly hosts legitimate product imagery "
                "— insufficient alone to indicate reuse fraud."
            )

        elif sim >= high_threshold:
            severity = "HIGH"
            evidence_strength = "HIGH"
            match_label = "Potential External Match"
            explanation = (
                f"Strong visual similarity ({sim_pct}%) detected against {source_domain}. "
                "Requires corroboration from additional independent signals."
            )

        elif sim >= medium_threshold:
            severity = "MEDIUM"
            evidence_strength = "MEDIUM"
            match_label = "Potential Source Match"
            explanation = f"Moderate visual similarity ({sim_pct}%) against {source_domain}."

        elif sim >= weak_threshold:
            severity = "LOW"
            evidence_strength = "LOW"
            match_label = "Weak Visual Match"
            explanation = f"Weak visual similarity ({sim_pct}%) — below threshold for meaningful evidence."

        else:
            severity = "LOW"
            evidence_strength = "LOW"
            match_label = "No Significant Match"
            explanation = f"Low visual similarity ({sim_pct}%). Candidate does not match merchant image."

        verified_list.append({
            "candidate_id": c.get("candidate_id", "cand_0"),
            "similarity": round(sim, 4),
            "similarity_pct": sim_pct,
            "severity": severity,
            "evidence_strength": evidence_strength,
            "match_label": match_label,
            "source_type": source_type,
            "source_url": source_url,
            "source_domain": source_domain,
            "title": title,
            "image": cand_img,
            "filename": c.get("filename"),
            "local_path": c.get("local_path"),
            "explanation": explanation,
            "is_self_domain": is_self_domain,
            "is_soft_trust": is_soft or is_supplier,
        })

    # Sort: genuine meaningful external matches (above weak threshold) first, then by similarity descending
    verified_list.sort(
        key=lambda x: (
            not x.get("is_self_domain", False),
            (x["similarity"] >= weak_threshold and not x.get("is_soft_trust", False)),
            x["similarity"],
        ),
        reverse=True,
    )

    external_candidates = [c for c in verified_list if not c.get("is_self_domain", False)]
    meaningful_externals = [
        c for c in external_candidates
        if not c.get("is_soft_trust", False) and c["similarity"] >= weak_threshold
    ]

    strong_meaningful = [c for c in meaningful_externals if c["similarity"] >= high_threshold]
    moderate_meaningful = [c for c in meaningful_externals if c["similarity"] >= medium_threshold]

    top_external = external_candidates[0] if external_candidates else None
    top_meaningful = meaningful_externals[0] if meaningful_externals else None

    max_sim_meaningful = top_meaningful["similarity"] if top_meaningful else 0.0
    max_sim_any = top_external["similarity"] if top_external else (verified_list[0]["similarity"] if verified_list else 0.0)

    # ---- 4-Status Taxonomy --------------------------------------------------
    if max_sim_any < weak_threshold:
        match_status = "NO_EXTERNAL_MATCH"
        is_own_brand = True
        active_top = verified_list[0] if verified_list else None

    elif max_sim_any < medium_threshold:
        match_status = "WEAK_MATCH"
        is_own_brand = True
        active_top = top_external

    elif len(strong_meaningful) >= 2 or (len(strong_meaningful) >= 1 and len(moderate_meaningful) >= 2):
        # Truly corroborated: multiple strong non-soft-trust matches
        match_status = "CORROBORATED_EXTERNAL_MATCH"
        is_own_brand = False
        active_top = top_meaningful

    elif len(meaningful_externals) == 0 and max_sim_any >= medium_threshold:
        # ONLY soft-trust matches (Pinterest, marketplace, stock, aggregator)
        # regardless of how high the similarity — INSUFFICIENT (T9 scenario)
        match_status = "INSUFFICIENT_EVIDENCE"
        is_own_brand = False
        active_top = dict(top_external) if top_external else None
        if active_top:
            active_top["explanation"] = (
                f"High visual similarity ({active_top['similarity_pct']}%) detected on soft-trust source "
                f"({active_top['source_domain']}). This source type commonly hosts legitimate product imagery "
                "— insufficient evidence alone to conclude malicious reuse."
            )
            active_top["evidence_strength"] = "LOW"

    elif len(strong_meaningful) == 1 and len(moderate_meaningful) < 2:
        # Single meaningful strong match, no secondary support
        match_status = "INSUFFICIENT_EVIDENCE"
        is_own_brand = False
        active_top = dict(top_meaningful) if top_meaningful else None
        if active_top:
            active_top["explanation"] = (
                f"Single strong match ({active_top['similarity_pct']}%) on {active_top['source_domain']}. "
                "Insufficient corroborating evidence to conclude meaningful reuse."
            )
            active_top["evidence_strength"] = "MEDIUM"

    elif len(moderate_meaningful) >= 1:
        match_status = "INSUFFICIENT_EVIDENCE"
        is_own_brand = False
        active_top = dict(top_meaningful) if top_meaningful else None
        if active_top:
            active_top["explanation"] = (
                f"Moderate similarity ({active_top['similarity_pct']}%) on {active_top['source_domain']}. "
                "Evidence present but not corroborated enough to establish reuse."
            )

    else:
        match_status = "INSUFFICIENT_EVIDENCE"
        is_own_brand = False
        active_top = top_external

    # ---- E4 Score: calibrated evidence score (0-100) ------------------------
    # NOT a fraud probability. Capped tightly for single/soft-trust matches.
    # A single Pinterest match at 0.96 sim -> e4_score <= 20, not >= 50.
    if match_status == "NO_EXTERNAL_MATCH":
        e4_score = 0.0
    elif match_status == "WEAK_MATCH":
        e4_score = min(20.0, max_sim_any * 30.0)
    elif match_status == "INSUFFICIENT_EVIDENCE":
        if len(meaningful_externals) == 0:
            # Soft-trust only: very low cap (T9: Pinterest 0.96 -> <= 20)
            e4_score = min(20.0, max_sim_any * 20.0)
        else:
            # Single meaningful match: capped at 35
            e4_score = min(35.0, 20.0 + (max_sim_meaningful - medium_threshold) / (1.0 - medium_threshold) * 15.0)
    elif match_status == "CORROBORATED_EXTERNAL_MATCH":
        base = 50.0 + (max_sim_meaningful - high_threshold) / (1.0 - high_threshold) * 20.0
        count_bonus = min(10.0, (len(strong_meaningful) - 1) * 5.0)
        e4_score = min(80.0, base + count_bonus)
    else:
        e4_score = 0.0

    e4_score = round(float(e4_score), 1)

    return {
        "top_candidate": active_top,
        "all_candidates": verified_list,
        "max_similarity": float(max_sim_meaningful if not is_own_brand else 0.0),
        "evidence_strength": active_top["evidence_strength"] if active_top else "LOW",
        "match_status": match_status,
        "is_own_brand_candidate": is_own_brand,
        "source_type": active_top["source_type"] if active_top else "NONE",
        "strong_match_count": len(strong_meaningful),
        "moderate_match_count": len(moderate_meaningful),
        "e4_score": e4_score,
        "explanation": active_top["explanation"] if active_top else "No external matches verified online (Own-Brand / Unique Content).",
    }
