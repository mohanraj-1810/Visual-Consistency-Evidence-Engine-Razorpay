"""
image_reuse.py — Visual Reuse Detection Engine.
Compares merchant product images against a reference catalog dataset
using ViT cosine similarity to detect potential image reuse / scraping.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from PIL import Image
import numpy as np

from visual.vit_embeddings import get_image_embedding, compute_cosine_similarity


# Global cache for reference database embeddings
_REFERENCE_CACHE: Dict[str, Tuple[np.ndarray, str]] = {}


def load_reference_dataset(reference_dir: Union[str, Path]) -> Dict[str, Tuple[np.ndarray, str]]:
    """
    Load all images from the reference directory and compute their embeddings.
    Caches results in memory for fast comparisons.

    Returns
    -------
    Dict mapping filename -> (embedding_vector, absolute_path)
    """
    global _REFERENCE_CACHE
    ref_path = Path(reference_dir)
    if not ref_path.exists():
        return {}

    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    files = [f for f in ref_path.iterdir() if f.is_file() and f.suffix.lower() in valid_extensions]

    for file_path in files:
        fname = file_path.name
        if fname not in _REFERENCE_CACHE:
            try:
                emb = get_image_embedding(str(file_path))
                _REFERENCE_CACHE[fname] = (emb, str(file_path))
            except Exception as e:
                continue

    return _REFERENCE_CACHE


def analyze_image_reuse(
    merchant_image: Union[Image.Image, str, np.ndarray],
    reference_dir: Union[str, Path] = "dataset/reference",
    high_threshold: float = 0.85,
    medium_threshold: float = 0.70,
) -> Dict:
    """
    Compare a single merchant image against reference dataset.

    Returns
    -------
    dict with keys:
        similarity: float (0.0 to 1.0)
        reference_filename: str or None
        reference_path: str or None
        risk_level: 'HIGH' | 'MEDIUM' | 'LOW'
        explanation: str
        all_matches: list of top matches
    """
    ref_db = load_reference_dataset(reference_dir)

    if not ref_db:
        return {
            "similarity": 0.0,
            "reference_filename": None,
            "reference_path": None,
            "risk_level": "LOW",
            "explanation": "No reference images available in catalog for comparison.",
            "all_matches": [],
        }

    merchant_emb = get_image_embedding(merchant_image)

    matches = []
    for fname, (ref_emb, ref_fpath) in ref_db.items():
        sim = compute_cosine_similarity(merchant_emb, ref_emb)
        matches.append({
            "filename": fname,
            "path": ref_fpath,
            "similarity": round(float(sim), 4),
        })

    # Sort descending by similarity
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    best_match = matches[0] if matches else {"similarity": 0.0, "filename": None, "path": None}

    max_sim = best_match["similarity"]
    best_fname = best_match["filename"]
    best_path = best_match["path"]

    if max_sim >= high_threshold:
        risk_level = "HIGH"
        pct = int(round(max_sim * 100))
        explanation = (
            f"Potential visual reuse detected ({pct}% similarity). "
            f"Merchant product visual strongly matches catalog reference: {best_fname}."
        )
    elif max_sim >= medium_threshold:
        risk_level = "MEDIUM"
        pct = int(round(max_sim * 100))
        explanation = (
            f"Moderate visual similarity detected ({pct}%). "
            f"Product exhibits strong visual commonalities with reference: {best_fname}."
        )
    else:
        risk_level = "LOW"
        pct = int(round(max_sim * 100))
        explanation = (
            f"No significant visual reuse detected. Closest catalog match is {pct}% ({best_fname})."
        )

    return {
        "similarity": float(max_sim),
        "reference_filename": best_fname,
        "reference_path": best_path,
        "risk_level": risk_level,
        "explanation": explanation,
        "all_matches": matches[:5],
    }


def analyze_multiple_images_reuse(
    merchant_images: List[Union[Image.Image, str]],
    reference_dir: Union[str, Path] = "dataset/reference",
) -> Dict:
    """
    Analyze a batch of merchant images and compute aggregate image reuse risk.
    """
    if not merchant_images:
        return {
            "max_similarity": 0.0,
            "average_similarity": 0.0,
            "reuse_risk_score": 0.0,
            "risk_level": "LOW",
            "findings": [],
            "top_flagged_item": None,
        }

    findings = []
    sims = []

    for idx, img in enumerate(merchant_images):
        res = analyze_image_reuse(img, reference_dir=reference_dir)
        res["image_index"] = idx
        findings.append(res)
        sims.append(res["similarity"])

    max_sim = max(sims) if sims else 0.0
    avg_sim = float(np.mean(sims)) if sims else 0.0

    # Risk score maps 0.0-1.0 similarity nonlinearly to 0-100 risk
    # High similarity (>0.85) yields risk score 80-100
    if max_sim >= 0.85:
        reuse_score = min(100.0, 75.0 + (max_sim - 0.85) / 0.15 * 25.0)
        overall_risk = "HIGH"
    elif max_sim >= 0.70:
        reuse_score = 40.0 + (max_sim - 0.70) / 0.15 * 35.0
        overall_risk = "MEDIUM"
    else:
        reuse_score = (max_sim / 0.70) * 39.0
        overall_risk = "LOW"

    # Find highest matching item
    top_flagged = max(findings, key=lambda x: x["similarity"]) if findings else None

    return {
        "max_similarity": float(max_sim),
        "average_similarity": float(avg_sim),
        "reuse_risk_score": round(float(reuse_score), 1),
        "risk_level": overall_risk,
        "findings": findings,
        "top_flagged_item": top_flagged,
    }


def compute_identity_coherence(
    product_images: List[Union[Image.Image, str, np.ndarray]],
    reference_dir: Union[str, Path] = "dataset/reference",
) -> Dict[str, Any]:
    """
    Measures how visually consistent a merchant's own product images are
    with each other, using pairwise cosine similarity of their ViT
    embeddings. High coherence = images look like they belong to the
    same coherent brand/catalog. Low coherence = images look like they
    were pulled from unrelated/inconsistent sources.

    Returns a dict:
        {
            "coherence_score": float (0-100),
            "explanation": str,
            "pairwise_similarities": list of floats,
        }
    """
    if not product_images or len(product_images) < 2:
        return {
            "coherence_score": 70.0,
            "explanation": "Insufficient images (< 2) to evaluate internal brand identity coherence. Neutral default applied.",
            "pairwise_similarities": [],
        }

    embeddings = []
    for img in product_images:
        try:
            emb = get_image_embedding(img)
            embeddings.append(emb)
        except Exception:
            continue

    if len(embeddings) < 2:
        return {
            "coherence_score": 70.0,
            "explanation": "Insufficient valid image embeddings (< 2) to evaluate internal brand identity coherence. Neutral default applied.",
            "pairwise_similarities": [],
        }

    pairwise_similarities = []
    n = len(embeddings)
    for i in range(n):
        for j in range(i + 1, n):
            sim = compute_cosine_similarity(embeddings[i], embeddings[j])
            pairwise_similarities.append(float(sim))

    if not pairwise_similarities:
        avg_sim = 0.70
    else:
        avg_sim = float(np.mean(pairwise_similarities))

    coherence_score = round(float(avg_sim * 100.0), 1)
    coherence_score = max(0.0, min(100.0, coherence_score))

    pct = int(round(coherence_score))
    if coherence_score >= 80.0:
        explanation = f"Merchant's product images show strong internal visual consistency (average pairwise similarity: {pct}%)."
    elif coherence_score >= 55.0:
        explanation = f"Merchant's product images show moderate internal visual consistency (average pairwise similarity: {pct}%)."
    else:
        explanation = f"Merchant's product images show low internal visual consistency, images may originate from different sources (average pairwise similarity: {pct}%)."

    return {
        "coherence_score": float(coherence_score),
        "explanation": explanation,
        "pairwise_similarities": [round(float(s), 4) for s in pairwise_similarities],
    }

