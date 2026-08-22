"""
verifier.py — ViT-based Visual Similarity Verification for Candidate Evidence.
Verifies candidate online images using Vision Transformer (ViT) embeddings
and cosine similarity. Never blindly trusts search results alone.
Distinguishes own-brand unique visuals from potential external reuse.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from PIL import Image
import numpy as np

from visual.vit_embeddings import get_image_embedding, compute_cosine_similarity


@dataclass
class CandidateMatch:
    candidate_id: str
    similarity: float
    similarity_pct: int
    severity: str  # "HIGH", "MEDIUM", "LOW"
    source_type: str  # "ONLINE", "LOCAL_TEST_FIXTURE"
    source_url: str
    source_domain: str
    title: str
    image: Optional[Image.Image]
    explanation: str
    evidence_strength: str  # "HIGH", "MEDIUM", "LOW"
    match_label: str  # "Potential External Match" | "Potential Source Match" | "No Significant Match"


def verify_candidates_with_vit(
    merchant_image: Union[Image.Image, np.ndarray, str],
    candidates: List[Dict[str, Any]],
    high_threshold: float = 0.85,
    medium_threshold: float = 0.70,
    merchant_domain: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Passes discovered online candidates through our ViT similarity verifier.

    Parameters
    ----------
    merchant_image : Merchant's product image
    candidates : List of candidate dicts from candidate_search
    high_threshold : Cosine similarity threshold for strong visual match
    medium_threshold : Cosine similarity threshold for moderate visual match
    merchant_domain : Optional domain string to filter out self-referencing candidates

    Returns
    -------
    dict with:
        top_candidate: dict or None
        all_candidates: List of candidate dicts
        max_similarity: float
        evidence_strength: str ("HIGH" | "MEDIUM" | "LOW")
        match_status: str ("EXTERNAL_MATCH_FOUND" | "NO_EXTERNAL_MATCH")
        is_own_brand_candidate: bool
        source_type: str ('ONLINE' or 'LOCAL_TEST_FIXTURE' or 'NONE')
        explanation: str
    """
    if not candidates:
        return {
            "top_candidate": None,
            "all_candidates": [],
            "max_similarity": 0.0,
            "evidence_strength": "LOW",
            "match_status": "NO_EXTERNAL_MATCH",
            "is_own_brand_candidate": True,
            "source_type": "NONE",
            "explanation": "No external visual matches discovered online. Visual content appears unique / proprietary to the merchant.",
        }

    try:
        merchant_emb = get_image_embedding(merchant_image)
    except Exception as e:
        return {
            "top_candidate": None,
            "all_candidates": [],
            "max_similarity": 0.0,
            "evidence_strength": "LOW",
            "match_status": "NO_EXTERNAL_MATCH",
            "is_own_brand_candidate": True,
            "source_type": "NONE",
            "explanation": f"ViT feature extraction notice: {str(e)}",
        }

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

        # Check for self-referencing domain
        is_self_domain = False
        if clean_merchant_domain and (
            clean_merchant_domain in source_domain
            or source_domain in clean_merchant_domain
            or clean_merchant_domain.split(".")[0] in source_domain.split(".")[0]
        ):
            is_self_domain = True

        # Combine visual similarity with source reliability to determine evidence strength
        if is_self_domain:
            severity = "LOW"
            evidence_strength = "LOW"
            match_label = "Own Domain / Brand Verified"
            explanation = (
                f"Verified merchant's own domain asset on {source_domain} ({sim_pct}% match)."
            )
        elif sim >= high_threshold:
            severity = "HIGH"
            evidence_strength = "HIGH"
            match_label = "Potential External Match"
            explanation = (
                f"Potential External Match ({sim_pct}% ViT similarity). "
                f"Merchant visual demonstrates strong visual commonality with external candidate on {source_domain}."
            )
        elif sim >= medium_threshold:
            severity = "MEDIUM"
            evidence_strength = "MEDIUM"
            match_label = "Potential Source Match"
            explanation = (
                f"Potential Source Match ({sim_pct}% ViT similarity). "
                f"Moderate visual similarity observed against candidate visual on {source_domain}."
            )
        else:
            severity = "LOW"
            evidence_strength = "LOW"
            match_label = "No Significant Match"
            explanation = (
                f"Low visual similarity ({sim_pct}%). "
                f"External candidate on {source_domain} does not match merchant image."
            )

        match_obj = {
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
        }
        verified_list.append(match_obj)

    # Sort descending by similarity, prioritizing genuine external matches
    verified_list.sort(key=lambda x: (not x.get("is_self_domain", False), x["similarity"]), reverse=True)

    # Find top external candidate
    external_candidates = [c for c in verified_list if not c.get("is_self_domain", False)]
    top_external = external_candidates[0] if external_candidates else None
    top_cand = verified_list[0] if verified_list else None
    
    max_sim = top_external["similarity"] if top_external else (top_cand["similarity"] if top_cand else 0.0)

    if top_external and max_sim >= medium_threshold:
        match_status = "EXTERNAL_MATCH_FOUND"
        is_own_brand = False
        active_top = top_external
    else:
        match_status = "NO_EXTERNAL_MATCH"
        is_own_brand = True
        active_top = top_cand

    return {
        "top_candidate": active_top,
        "all_candidates": verified_list,
        "max_similarity": float(max_sim if not is_own_brand else 0.0),
        "evidence_strength": active_top["evidence_strength"] if active_top else "LOW",
        "match_status": match_status,
        "is_own_brand_candidate": is_own_brand,
        "source_type": active_top["source_type"] if active_top else "NONE",
        "explanation": active_top["explanation"] if active_top else "No external matches verified online (Own-Brand / Unique Content).",
    }
