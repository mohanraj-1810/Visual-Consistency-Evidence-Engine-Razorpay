"""
logo_check.py — Logo and Brand Identity Visual Consistency Engine.
Compares a merchant's logo against verified reference brand logos
stored in dataset/logos/ to evaluate visual identity consistency.
Does NOT claim trademark infringement or fraud.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image
import numpy as np

from visual.vit_embeddings import get_image_embedding, compute_cosine_similarity


def load_verified_logos(logos_dir: Union[str, Path] = "dataset/logos") -> Dict[str, Tuple[np.ndarray, str]]:
    """
    Load all verified reference logos and compute their embeddings.
    """
    path = Path(logos_dir)
    if not path.exists():
        return {}

    valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    logos = {}
    for f in path.iterdir():
        if f.is_file() and f.suffix.lower() in valid_exts:
            try:
                emb = get_image_embedding(str(f))
                logos[f.name] = (emb, str(f))
            except Exception:
                continue
    return logos


def check_logo_consistency(
    merchant_logo: Union[Image.Image, str, np.ndarray],
    claimed_brand: Optional[str] = None,
    logos_dir: Union[str, Path] = "dataset/logos",
) -> Dict:
    """
    Compare merchant logo against verified reference logos.

    Parameters
    ----------
    merchant_logo : PIL.Image or path
    claimed_brand : Optional brand name string to target specific verified logo
    logos_dir : Directory with verified logos

    Returns
    -------
    dict with keys:
        similarity: float (0.0 to 1.0)
        consistency_score: float (0.0 to 100.0) [100 = completely consistent]
        risk_level: 'HIGH' | 'MEDIUM' | 'LOW'
        inconsistency_risk: float (0.0 to 100.0) [100 = highest inconsistency risk]
        matched_reference: str or None
        matched_path: str or None
        explanation: str
    """
    verified_logos = load_verified_logos(logos_dir)

    if not verified_logos:
        return {
            "similarity": 1.0,
            "consistency_score": 100.0,
            "inconsistency_risk": 0.0,
            "risk_level": "LOW",
            "matched_reference": None,
            "matched_path": None,
            "explanation": "No verified reference logos registered in repository for brand comparison.",
        }

    logo_emb = get_image_embedding(merchant_logo)

    # ── Brand-Relevant Filtering ──────────────────────────────────────────────
    # Only compare against logos whose filename partially matches the claimed brand.
    # If no relevant reference exists, return NEUTRAL (LOW risk) — comparing against
    # unrelated brands (e.g. Apple logo vs pottery brand logo) produces false positives.
    brand_matched_items = []
    if claimed_brand:
        brand_clean = claimed_brand.lower().replace(" ", "").replace("-", "").replace("_", "")
        brand_words = [w for w in claimed_brand.lower().split() if len(w) > 2]
        for fname, (ref_emb, ref_fpath) in verified_logos.items():
            fname_clean = fname.lower().replace(" ", "").replace("-", "").replace("_", "")
            # Check if brand name is contained in filename or vice versa
            if brand_clean in fname_clean or fname_clean.replace(".png", "").replace(".jpg", "") in brand_clean:
                brand_matched_items.append((fname, ref_emb, ref_fpath))
            elif any(bw in fname_clean for bw in brand_words if len(bw) > 3):
                brand_matched_items.append((fname, ref_emb, ref_fpath))

    # If no brand-relevant reference logos exist, return neutral LOW risk.
    # Comparing against unrelated reference logos produces misleading scores.
    if not brand_matched_items:
        return {
            "similarity": 0.85,
            "consistency_score": 85.0,
            "inconsistency_risk": 15.0,
            "risk_level": "LOW",
            "matched_reference": None,
            "matched_path": None,
            "explanation": (
                "No registered brand reference logo available for the claimed identity. "
                "Logo consistency cannot be evaluated without a verified reference. Neutral risk assigned."
            ),
        }

    # Compare against brand-relevant references only
    comparisons = []
    for fname, ref_emb, ref_fpath in brand_matched_items:
        sim = compute_cosine_similarity(logo_emb, ref_emb)
        comparisons.append({
            "name": fname,
            "path": ref_fpath,
            "similarity": round(float(sim), 4),
        })

    comparisons.sort(key=lambda x: x["similarity"], reverse=True)
    best = comparisons[0] if comparisons else {"name": None, "path": None, "similarity": 0.0}

    sim = best["similarity"]
    best_name = best["name"]
    best_path = best["path"]

    # When merchant claims to be a brand, low similarity to official logo = HIGH risk
    # If similarity is high (>0.80), logo is consistent with reference -> LOW risk
    consistency_score = round(sim * 100.0, 1)
    inconsistency_risk = round(max(0.0, (1.0 - sim) * 100.0), 1)

    if sim >= 0.82:
        risk_level = "LOW"
        explanation = (
            f"Merchant logo demonstrates strong visual consistency ({consistency_score}%) "
            f"with verified reference identity ({best_name})."
        )
    elif sim >= 0.55:
        risk_level = "MEDIUM"
        explanation = (
            f"Merchant logo demonstrates moderate visual variance ({consistency_score}% match) "
            f"against verified reference identity ({best_name})."
        )
    else:
        risk_level = "HIGH"
        explanation = (
            f"Merchant logo shows low visual similarity ({consistency_score}%) "
            f"to the verified reference identity ({best_name})."
        )

    return {
        "similarity": float(sim),
        "consistency_score": float(consistency_score),
        "inconsistency_risk": float(inconsistency_risk),
        "risk_level": risk_level,
        "matched_reference": best_name,
        "matched_path": best_path,
        "explanation": explanation,
        "all_comparisons": comparisons,
    }
