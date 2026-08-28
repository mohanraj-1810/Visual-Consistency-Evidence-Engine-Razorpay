"""
services/logo_detector.py — Automatic Logo and Brand Consistency Engine.
Compares extracted merchant logo against verified brand references using ViT embeddings.
Guarantees that uncorroborated open-web noise does not trigger false logo mismatch penalties,
and marks status as UNAVAILABLE when trusted brand data is absent.
"""

from __future__ import annotations

from typing import Dict, Optional, Any, Tuple
from PIL import Image

from visual.vit_embeddings import get_image_embedding, compute_cosine_similarity
from services.verified_brand_resolver import resolve_verified_brand_logo


def verify_merchant_logo(
    logo_image: Optional[Image.Image],
    logo_url: Optional[str],
    claimed_brand: Optional[str],
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Verifies merchant logo against official verified brand records.

    Returns
    -------
    (brand_verification_status, evidence_item or None)
    where brand_verification_status is 'VERIFIED' | 'UNAVAILABLE'.
    """
    if logo_image is None or not claimed_brand:
        return "UNAVAILABLE", None

    status, verified_logo, matched_name = resolve_verified_brand_logo(claimed_brand)
    if status == "UNAVAILABLE" or verified_logo is None:
        return "UNAVAILABLE", None

    try:
        merchant_emb = get_image_embedding(logo_image)
        ref_emb = get_image_embedding(verified_logo)
        sim = float(compute_cosine_similarity(merchant_emb, ref_emb))
    except Exception:
        return "UNAVAILABLE", None

    sim_pct = int(round(sim * 100))

    if sim < 0.60:
        # High divergence from verified logo
        mismatch_score = int(round((1.0 - sim) * 100))
        explanation = (
            f"Potential logo mismatch ({sim_pct}% visual match with verified {matched_name} logo). "
            f"Extracted website logo exhibits notable visual divergence from registered brand asset."
        )
        evidence = {
            "asset_url": logo_url or "merchant_logo",
            "asset_type": "logo",
            "signal_type": "potential_logo_mismatch",
            "score": mismatch_score,
            "matched_pages": [],
            "matched_images": [],
            "explanation": explanation,
            "heatmap_url": None,
        }
        return "VERIFIED", evidence
    elif sim < 0.78:
        # Moderate variation
        mismatch_score = int(round((0.80 - sim) * 50))
        explanation = (
            f"Moderate visual variation ({sim_pct}% match with verified {matched_name} logo). "
            f"Logo style or format variant detected."
        )
        evidence = {
            "asset_url": logo_url or "merchant_logo",
            "asset_type": "logo",
            "signal_type": "potential_logo_mismatch",
            "score": mismatch_score,
            "matched_pages": [],
            "matched_images": [],
            "explanation": explanation,
            "heatmap_url": None,
        }
        return "VERIFIED", evidence
    else:
        # Strong match
        explanation = f"Extracted logo matches verified official {matched_name} brand asset ({sim_pct}% similarity)."
        evidence = {
            "asset_url": logo_url or "merchant_logo",
            "asset_type": "logo",
            "signal_type": "potential_logo_mismatch",
            "score": 0,
            "matched_pages": [],
            "matched_images": [],
            "explanation": explanation,
            "heatmap_url": None,
        }
        return "VERIFIED", evidence
