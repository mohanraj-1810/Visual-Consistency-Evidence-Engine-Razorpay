"""
services/evidence_fusion.py — Dual Evidence Fusion & Local ViT Visual-Similarity Index.
Fuses Google Cloud Vision Web Detection and Local Cross-Merchant ViT Embeddings.

Fusion Principles:
- Uses source-specific thresholds (Google Vision full/page match vs ViT cosine similarity >= 0.88).
- Records raw provider provenance before normalization.
- Separates asset-level evidence classification (LOW_EVIDENCE, POTENTIAL_REUSE, CORROBORATED_POTENTIAL_REUSE)
  from merchant-level decision (NORMAL_FLOW, ADDITIONAL_VERIFICATION, MANUAL_REVIEW).
- ViT index queries exclude current merchant_id, current domain, and asset hash.
- Post-analysis indexing: new asset embeddings are indexed ONLY after report generation.
- Uses strictly safe phrasing: "corroborated potential visual reuse evidence".
"""

from __future__ import annotations

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image
import numpy as np

from visual.vit_embeddings import get_image_embedding, compute_cosine_similarity
from services.evidence_normalizer import _extract_domain, is_self_referencing_domain, is_marketplace_domain, is_stock_domain


# Persistent / In-memory local ViT cross-merchant index
# asset_hash -> {
#   "embedding": np.ndarray,
#   "merchant_id": str,
#   "domain": str,
#   "asset_url": str,
#   "asset_type": str,
#   "timestamp": float,
# }
_LOCAL_VIT_INDEX: Dict[str, Dict[str, Any]] = {}
_VIT_STRONG_MATCH_THRESHOLD = 0.88  # Cosine similarity for near-duplicate cross-merchant visual match
_VIT_MODERATE_MATCH_THRESHOLD = 0.75


def mask_merchant_id(merchant_id: str) -> str:
    """Masks merchant identifier for privacy (e.g. 'merchant_001' -> 'mch_***001')."""
    if not merchant_id:
        return "mch_***"
    clean = str(merchant_id).strip()
    if len(clean) <= 4:
        return f"mch_***{clean[-2:]}"
    return f"mch_***{clean[-4:]}"


def init_local_vit_index(reference_dir: Optional[str] = None):
    """Pre-populates local ViT index from initial reference merchant catalog if empty."""
    global _LOCAL_VIT_INDEX
    if _LOCAL_VIT_INDEX:
        return

    base_dir = Path(__file__).resolve().parent.parent
    ref_path = Path(reference_dir) if reference_dir else base_dir / "dataset" / "reference"
    
    if not ref_path.exists():
        return

    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
    for idx, f in enumerate(ref_path.iterdir()):
        if f.is_file() and f.suffix.lower() in valid_exts:
            try:
                emb = get_image_embedding(str(f))
                fake_mch_id = f"mch_prev_{idx+1:03d}"
                _LOCAL_VIT_INDEX[f.name] = {
                    "embedding": emb,
                    "merchant_id": fake_mch_id,
                    "domain": "catalog-platform.internal",
                    "asset_url": f"/dataset/reference/{f.name}",
                    "asset_type": "product_image",
                    "timestamp": time.time(),
                }
            except Exception:
                continue


# Initialize reference pool
init_local_vit_index()


def query_local_vit_index(
    asset_image: Image.Image,
    current_merchant_id: str,
    current_domain: Optional[str],
    current_asset_hash: Optional[str],
    limit: int = 5,
) -> Tuple[float, List[Dict[str, Any]], str]:
    """
    Queries local cross-merchant ViT index with strict exclusion of:
      - current merchant_id
      - current domain
      - current asset hash

    Returns
    -------
    (max_similarity, matched_merchants_list, vit_provider_result)
    """
    if not _LOCAL_VIT_INDEX:
        return 0.0, [], "none"

    try:
        query_emb = get_image_embedding(asset_image)
    except Exception:
        return 0.0, [], "none"

    matches = []
    clean_domain = current_domain.lower().replace("www.", "").strip() if current_domain else ""

    for asset_key, indexed in _LOCAL_VIT_INDEX.items():
        # Exclude 1: Same asset hash
        if current_asset_hash and asset_key == current_asset_hash:
            continue

        # Exclude 2: Same merchant ID
        if indexed["merchant_id"] == current_merchant_id:
            continue

        # Exclude 3: Same domain
        idx_domain = indexed.get("domain", "").lower().replace("www.", "").strip()
        if clean_domain and (idx_domain == clean_domain or idx_domain.endswith("." + clean_domain)):
            continue

        sim = float(compute_cosine_similarity(query_emb, indexed["embedding"]))
        if sim >= _VIT_MODERATE_MATCH_THRESHOLD:
            matches.append({
                "merchant_id": indexed["merchant_id"],
                "masked_merchant_id": mask_merchant_id(indexed["merchant_id"]),
                "domain": indexed.get("domain", "previous-merchant.com"),
                "asset_url": indexed.get("asset_url", ""),
                "similarity": round(sim, 4),
                "is_strong_match": sim >= _VIT_STRONG_MATCH_THRESHOLD,
            })

    matches.sort(key=lambda x: x["similarity"], reverse=True)
    top_sim = matches[0]["similarity"] if matches else 0.0

    if top_sim >= _VIT_STRONG_MATCH_THRESHOLD:
        provider_result = "near_duplicate_match"
    elif top_sim >= _VIT_MODERATE_MATCH_THRESHOLD:
        provider_result = "similar_image"
    else:
        provider_result = "none"

    return top_sim, matches[:limit], provider_result


def fuse_asset_evidence(
    asset_image: Image.Image,
    meta: Dict[str, Any],
    web_detection_result: Dict[str, Any],
    current_merchant_id: str,
    current_domain: Optional[str],
) -> Dict[str, Any]:
    """
    Fuses Google Cloud Vision Web Detection and Local ViT Cross-Merchant matches.
    Determines asset-level evidence classification and builds complete provenance metadata.
    """
    asset_url = meta.get("src", "")
    asset_type = meta.get("asset_type", "product_image")
    asset_hash = meta.get("sha256")

    # 1. Google Cloud Vision open-web analysis
    full_matches = web_detection_result.get("full_matching_images", [])
    partial_matches = web_detection_result.get("partial_matching_images", [])
    similar_images = web_detection_result.get("visually_similar_images", [])
    all_matched_images = full_matches + partial_matches

    raw_pages = web_detection_result.get("pages_with_matching_images", [])
    matched_pages = []
    matched_domains = []

    for page in raw_pages:
        p_url = page.get("url", "")
        p_domain = _extract_domain(p_url)
        if p_url and not is_self_referencing_domain(p_domain, current_domain):
            matched_pages.append({"url": p_url, "domain": p_domain})
            if p_domain not in matched_domains:
                matched_domains.append(p_domain)

    # Google Vision raw provider result
    if full_matches or (matched_pages and len(full_matches) > 0):
        gv_provider_result = "full_match"
        gv_score = 75 if not any(is_marketplace_domain(d) for d in matched_domains) else 60
    elif partial_matches or matched_pages:
        gv_provider_result = "partial_match"
        gv_score = 50 if not any(is_marketplace_domain(d) for d in matched_domains) else 45
    elif similar_images:
        gv_provider_result = "similar_image"
        gv_score = 30
    else:
        gv_provider_result = "none"
        gv_score = 0

    # 2. Local ViT cross-merchant similarity
    vit_sim, matched_merchants, vit_provider_result = query_local_vit_index(
        asset_image=asset_image,
        current_merchant_id=current_merchant_id,
        current_domain=current_domain,
        current_asset_hash=asset_hash,
    )
    vit_score = int(round(vit_sim * 100)) if vit_sim >= _VIT_MODERATE_MATCH_THRESHOLD else 0
    matched_mch_ids = [m["merchant_id"] for m in matched_merchants]
    masked_mch_ids = [m["masked_merchant_id"] for m in matched_merchants]

    # 3. Source-specific strong match criteria
    is_gv_strong = (gv_provider_result == "full_match") or (len(matched_pages) >= 1 and gv_score >= 50)
    is_vit_strong = (vit_sim >= _VIT_STRONG_MATCH_THRESHOLD)

    has_open_web = gv_score > 0
    has_local_vit = vit_score > 0

    # 4. Evidence Source & Corroboration Determination
    if is_gv_strong and is_vit_strong:
        corroborated = True
        evidence_source = "FUSED"
        confidence = "HIGH"
        asset_evidence_level = "CORROBORATED_POTENTIAL_REUSE"
        signal_type = "external_image_reuse"
        composite_score = min(85, int(round(0.5 * gv_score + 0.5 * vit_score + 15)))
        explanation = (
            f"This asset has corroborated potential visual reuse evidence across both the open web "
            f"({', '.join(matched_domains[:2]) if matched_domains else 'external domains'}) and "
            f"strong visual similarity ({int(round(vit_sim*100))}%) to visuals from previously scanned merchant(s)."
        )
    elif has_open_web and has_local_vit:
        corroborated = True
        evidence_source = "FUSED"
        confidence = "MEDIUM"
        asset_evidence_level = "CORROBORATED_POTENTIAL_REUSE"
        signal_type = "external_image_reuse"
        composite_score = min(70, int(round(0.5 * gv_score + 0.5 * vit_score + 10)))
        explanation = (
            f"Potential visual reuse evidence: partial matches discovered on open web and moderate "
            f"cross-merchant visual similarity ({int(round(vit_sim*100))}%)."
        )
    elif has_open_web:
        corroborated = False
        evidence_source = "OPEN_WEB"
        confidence = "HIGH" if is_gv_strong else "MEDIUM"
        asset_evidence_level = "POTENTIAL_REUSE"
        signal_type = "external_image_reuse"
        composite_score = min(60, gv_score)  # Capped: open-web alone cannot independently cause HIGH risk
        explanation = (
            f"Potential visual reuse evidence discovered on open web ({', '.join(matched_domains[:2]) if matched_domains else 'third-party pages'}). "
            f"No cross-merchant matches found in platform index."
        )
    elif has_local_vit:
        corroborated = False
        evidence_source = "LOCAL_INDEX"
        confidence = "HIGH" if is_vit_strong else "MEDIUM"
        asset_evidence_level = "POTENTIAL_REUSE"
        signal_type = "cross_merchant_visual_similarity"
        composite_score = min(58, vit_score)  # Capped: local ViT match alone cannot independently cause HIGH risk
        explanation = (
            f"Visual similarity observed against visual assets from previously scanned merchant ({', '.join(masked_mch_ids[:2])}). "
            f"No open-web matches found."
        )
    else:
        corroborated = False
        evidence_source = "FUSED"
        confidence = "LOW"
        asset_evidence_level = "LOW_EVIDENCE"
        signal_type = "external_image_reuse"
        composite_score = 0
        explanation = "Unique asset. No open web matches or cross-merchant visual commonalities detected."

    return {
        "asset_url": asset_url,
        "asset_type": asset_type,
        "signal_type": signal_type,
        "score": composite_score,
        "google_web_match_score": gv_score,
        "local_vit_similarity_score": vit_score,
        "google_vision_provider_result": gv_provider_result,
        "vit_cosine_similarity": round(vit_sim, 4),
        "matched_domains": matched_domains[:5],
        "matched_merchant_ids": matched_mch_ids[:5],
        "masked_merchant_ids": masked_mch_ids[:5],
        "evidence_source": evidence_source,
        "corroborated": corroborated,
        "confidence": confidence,
        "asset_evidence_level": asset_evidence_level,
        "matched_pages": matched_pages[:5],
        "matched_images": all_matched_images[:5],
        "explanation": explanation,
        "heatmap_url": None,  # Strict rule: No heatmap for visual reuse
    }


def index_analyzed_assets(
    assets_with_images: List[Tuple[Image.Image, Dict[str, Any]]],
    merchant_id: str,
    domain: str,
):
    """
    Inserts newly analyzed assets into the persistent ViT cross-merchant index.
    Executed strictly AFTER the final report has been generated.
    """
    global _LOCAL_VIT_INDEX
    for img, meta in assets_with_images:
        sha_hash = meta.get("sha256")
        if not sha_hash:
            continue
        try:
            emb = get_image_embedding(img)
            _LOCAL_VIT_INDEX[sha_hash] = {
                "embedding": emb,
                "merchant_id": merchant_id,
                "domain": domain,
                "asset_url": meta.get("src", ""),
                "asset_type": meta.get("asset_type", "product_image"),
                "timestamp": time.time(),
            }
        except Exception:
            continue
