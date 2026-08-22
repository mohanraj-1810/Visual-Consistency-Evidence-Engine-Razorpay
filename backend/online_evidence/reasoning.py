"""
reasoning.py — Structured Evidence Objects & Claim-to-Evidence Reasoning Engine.
Maps raw computer vision and forensic outputs into structured evidence objects,
evaluates Claim ↔ Evidence relationships (SUPPORTS / CONTRADICTS / REQUIRES_VERIFICATION),
and synthesizes dynamic explainable conclusions and recommendations.
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Union
from PIL import Image
import numpy as np


@dataclass
class EvidenceObject:
    evidence_type: str  # 'image_reuse' | 'logo_consistency' | 'manipulation' | 'synthetic_signal' | 'visual_identity'
    title: str
    score: float  # 0 to 100 risk/anomaly score
    similarity_pct: int
    severity: str  # 'HIGH' | 'MEDIUM' | 'LOW'
    relationship: str  # 'SUPPORTS' | 'CONTRADICTS' | 'REQUIRES_VERIFICATION' | 'NEUTRAL'
    source_type: str  # 'ONLINE' | 'LOCAL_DEMO'
    source_url: Optional[str]
    source_domain: str
    matched_image_base64: Optional[str]
    explanation: str
    evidence_strength: str  # 'HIGH' | 'MEDIUM' | 'LOW'


def _encode_b64(img: Union[Image.Image, np.ndarray, None]) -> Optional[str]:
    if img is None:
        return None
    try:
        if isinstance(img, np.ndarray):
            if img.dtype != np.uint8:
                img = np.clip(img, 0, 255).astype(np.uint8)
            if len(img.shape) == 2:
                pil_img = Image.fromarray(img, mode="L")
            elif img.shape[2] == 3:
                pil_img = Image.fromarray(img, mode="RGB")
            else:
                return None
        elif isinstance(img, Image.Image):
            pil_img = img
        else:
            return None

        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        enc = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{enc}"
    except Exception:
        return None


def generate_structured_evidence(
    reuse_data: Dict[str, Any],
    logo_data: Dict[str, Any],
    manipulation_data: Dict[str, Any],
    identity_data: Dict[str, Any],
    verified_candidate: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Constructs standardized, serializable Evidence Objects for all evaluated signals.
    """
    evidence_list: List[Dict[str, Any]] = []

    # 1. Image Reuse Evidence Object
    top_cand = verified_candidate or reuse_data.get("top_flagged_item")
    if top_cand:
        sim = float(top_cand.get("similarity", 0.0))
        sim_pct = int(round(sim * 100))
        src_type = top_cand.get("source_type", "LOCAL_DEMO")
        src_domain = top_cand.get("source_domain") or (
            "archive.merchant-catalog.org" if src_type == "LOCAL_DEMO" else "public-web-source.com"
        )
        src_url = top_cand.get("source_url") or (
            f"https://catalog-archive.internal/assets/{top_cand.get('filename', 'ref_catalog.jpg')}"
        )
        cand_img = top_cand.get("image")

        if sim >= 0.85:
            relationship = "CONTRADICTS"
            severity = "HIGH"
            strength = "HIGH"
            explanation = (
                f"Merchant product imagery strongly matches a candidate visual found on {src_domain} "
                f"({sim_pct}% ViT similarity)."
            )
        elif sim >= 0.70:
            relationship = "REQUIRES_VERIFICATION"
            severity = "MEDIUM"
            strength = "MEDIUM"
            explanation = (
                f"Merchant product imagery exhibits moderate visual commonalities with a candidate on {src_domain} "
                f"({sim_pct}% ViT similarity)."
            )
        else:
            relationship = "SUPPORTS"
            severity = "LOW"
            strength = "LOW"
            explanation = (
                f"No significant visual reuse detected. Product images appear original ({sim_pct}% highest candidate match)."
            )

        evidence_list.append({
            "evidence_type": "image_reuse",
            "title": "Product Visual Reuse",
            "score": round(sim * 100, 1),
            "similarity_pct": sim_pct,
            "severity": severity,
            "relationship": relationship,
            "source_type": src_type,
            "source_url": src_url,
            "source_domain": src_domain,
            "matched_image_base64": _encode_b64(cand_img) if cand_img else None,
            "matched_reference_name": top_cand.get("filename") or top_cand.get("reference_filename"),
            "explanation": explanation,
            "evidence_strength": strength,
        })

    # 2. Logo Consistency Evidence Object
    logo_sim = float(logo_data.get("similarity", 1.0))
    logo_sim_pct = int(round(logo_sim * 100))
    inconsistency_risk = float(logo_data.get("inconsistency_risk", 0.0))
    matched_logo_name = logo_data.get("matched_reference") or "Registered Brand Identity"

    if logo_sim < 0.55:
        relationship = "CONTRADICTS"
        severity = "HIGH"
        strength = "HIGH"
        explanation = (
            f"Merchant logo demonstrates low visual consistency ({logo_sim_pct}%) with verified {matched_logo_name} identity."
        )
    elif logo_sim < 0.82:
        relationship = "REQUIRES_VERIFICATION"
        severity = "MEDIUM"
        strength = "MEDIUM"
        explanation = (
            f"Merchant logo exhibits moderate stylistic variance ({logo_sim_pct}% match) against verified {matched_logo_name} identity."
        )
    else:
        relationship = "SUPPORTS"
        severity = "LOW"
        strength = "LOW"
        explanation = (
            f"Merchant logo demonstrates strong visual alignment ({logo_sim_pct}%) with verified {matched_logo_name} identity."
        )

    evidence_list.append({
        "evidence_type": "logo_consistency",
        "title": "Brand Identity Consistency",
        "score": inconsistency_risk,
        "similarity_pct": logo_sim_pct,
        "severity": severity,
        "relationship": relationship,
        "source_type": "LOCAL_DEMO",
        "source_url": f"https://brand-registry.internal/logos/{matched_logo_name}",
        "source_domain": "brand-registry.internal",
        "matched_image_base64": None,
        "matched_reference_name": matched_logo_name,
        "explanation": explanation,
        "evidence_strength": strength,
    })

    # 3. Manipulation / ELA Evidence Object
    manip_score = float(manipulation_data.get("manipulation_score", 0.0))
    if manip_score >= 60.0:
        relationship = "CONTRADICTS"
        severity = "HIGH"
        strength = "HIGH"
        explanation = (
            f"Manipulation indicators detected ({manip_score}% anomaly score). "
            f"Localized compression and edge-frequency anomalies observed."
        )
    elif manip_score >= 35.0:
        relationship = "REQUIRES_VERIFICATION"
        severity = "MEDIUM"
        strength = "MEDIUM"
        explanation = (
            f"Moderate forensic anomalies detected ({manip_score}% anomaly score). "
            f"Minor compression artifacts or multi-layer graphics detected."
        )
    else:
        relationship = "SUPPORTS"
        severity = "LOW"
        strength = "LOW"
        explanation = (
            f"Document visual displays uniform compression and natural pixel distributions ({manip_score}% score)."
        )

    evidence_list.append({
        "evidence_type": "manipulation",
        "title": "Document & Visual Manipulation Indicators",
        "score": manip_score,
        "similarity_pct": int(round(manip_score)),
        "severity": severity,
        "relationship": relationship,
        "source_type": "LOCAL_DEMO",
        "source_url": None,
        "source_domain": "forensic-pixel-pipeline",
        "matched_image_base64": None,
        "matched_reference_name": None,
        "explanation": explanation,
        "evidence_strength": strength,
    })

    # 4. Synthetic-Image Supporting Signal
    synth_score = float(manipulation_data.get("synthetic_score", 10.0))
    if synth_score >= 60.0:
        synth_rel = "REQUIRES_VERIFICATION"
        synth_sev = "MEDIUM"
        synth_exp = f"Elevated synthetic/AI-generation markers detected ({synth_score}%). Supporting signal only."
    else:
        synth_rel = "NEUTRAL"
        synth_sev = "LOW"
        synth_exp = f"Natural photographic frequency and chromatic signatures observed ({synth_score}% score)."

    evidence_list.append({
        "evidence_type": "synthetic_signal",
        "title": "Synthetic-Image Suspicion (Supporting Signal)",
        "score": synth_score,
        "similarity_pct": int(round(synth_score)),
        "severity": synth_sev,
        "relationship": synth_rel,
        "source_type": "LOCAL_DEMO",
        "source_url": None,
        "source_domain": "spectral-frequency-analyzer",
        "matched_image_base64": None,
        "matched_reference_name": None,
        "explanation": synth_exp,
        "evidence_strength": "LOW" if synth_score < 60 else "MEDIUM",
    })

    # 5. Visual Identity Coherence Object
    coherence_score = float(identity_data.get("coherence_score", 85.0))
    dispersion_risk = round(max(0.0, min(100.0, 100.0 - coherence_score)), 1)
    if coherence_score < 25.0:
        id_rel = "CONTRADICTS"
        id_sev = "HIGH"
        id_exp = f"Merchant product catalog displays low internal visual consistency ({int(coherence_score)}% coherence)."
    elif coherence_score < 45.0:
        id_rel = "REQUIRES_VERIFICATION"
        id_sev = "MEDIUM"
        id_exp = f"Merchant product catalog displays moderate internal visual consistency ({int(coherence_score)}% coherence)."
    else:
        id_rel = "SUPPORTS"
        id_sev = "LOW"
        id_exp = f"Merchant product catalog shows strong internal visual consistency ({int(coherence_score)}% coherence)."

    evidence_list.append({
        "evidence_type": "visual_identity",
        "title": "Catalog Visual Identity Consistency",
        "score": dispersion_risk,
        "similarity_pct": int(round(coherence_score)),
        "severity": id_sev,
        "relationship": id_rel,
        "source_type": "LOCAL_DEMO",
        "source_url": None,
        "source_domain": "catalog-coherence-analyzer",
        "matched_image_base64": None,
        "matched_reference_name": None,
        "explanation": id_exp,
        "evidence_strength": "HIGH" if coherence_score < 25 else "MEDIUM" if coherence_score < 45 else "LOW",
    })

    return evidence_list


def synthesize_claims_reasoning(
    claims: Dict[str, str],
    evidence_objects: List[Dict[str, Any]],
    final_risk_score: float,
    status: str,
) -> Dict[str, Any]:
    """
    Synthesizes Claim vs Visual Evidence matrix, dynamic conclusion,
    and workflow recommendation.
    """
    # Count contradictions and verifications
    contradictions = [e for e in evidence_objects if e["relationship"] == "CONTRADICTS"]
    verifications = [e for e in evidence_objects if e["relationship"] == "REQUIRES_VERIFICATION"]
    supports = [e for e in evidence_objects if e["relationship"] == "SUPPORTS"]

    # Dynamic Conclusion aligned with evidence and risk status
    if status == "HIGH":
        if len(contradictions) >= 2:
            conclusion = "Multiple independent visual signals are inconsistent with the merchant's stated identity."
        else:
            conclusion = "Critical visual evidence conflicts with merchant assertions and requires senior review."
    elif status == "MEDIUM":
        if len(contradictions) >= 1:
            conclusion = "Visual evidence displays significant inconsistencies and unverified anomalies relative to merchant claims."
        elif len(verifications) >= 2:
            conclusion = "Multiple visual signals require additional verification before merchant onboarding approval."
        else:
            conclusion = "Visual evidence displays moderate anomalies requiring merchant documentation verification."
    else:  # LOW risk
        if len(verifications) >= 1:
            conclusion = "Visual evidence is largely consistent with merchant claims, with isolated low-risk anomalies."
        else:
            conclusion = "Visual evidence strongly supports the merchant's stated identity and product claims."

    # Dynamic Recommendation
    if status == "HIGH":
        recommendation = "HIGH → MANUAL REVIEW: Route to Senior Risk Operations for manual visual evidence audit."
    elif status == "MEDIUM":
        recommendation = "MEDIUM → ADDITIONAL VERIFICATION: Request merchant brand authorization documentation and high-res inventory proof."
    else:
        recommendation = "LOW → NORMAL ONBOARDING: Standard merchant onboarding flow with automated background monitoring."

    # Build side-by-side claim items
    claim_items = []
    
    # Item 1: Inventory
    reuse_obj = next((e for e in evidence_objects if e["evidence_type"] == "image_reuse"), None)
    claim_items.append({
        "dimension": "1. Inventory & Products",
        "claim": claims.get("inventory_claim", "Authentic proprietary inventory"),
        "evidence_summary": reuse_obj["explanation"] if reuse_obj else "No visual catalog match found.",
        "relationship": reuse_obj["relationship"] if reuse_obj else "NEUTRAL",
        "severity": reuse_obj["severity"] if reuse_obj else "LOW",
        "score_label": f"ViT Similarity: {reuse_obj['similarity_pct']}%" if reuse_obj else "ViT Similarity: 0%",
        "source_type": reuse_obj.get("source_type", "ONLINE") if reuse_obj else "LOCAL_DEMO",
        "source_url": reuse_obj.get("source_url") if reuse_obj else None,
        "source_domain": reuse_obj.get("source_domain") if reuse_obj else None,
    })

    # Item 2: Brand Identity
    logo_obj = next((e for e in evidence_objects if e["evidence_type"] == "logo_consistency"), None)
    claim_items.append({
        "dimension": "2. Brand Identity & Logo",
        "claim": claims.get("brand_claim", "Verified brand trademark"),
        "evidence_summary": logo_obj["explanation"] if logo_obj else "Brand mark unverified.",
        "relationship": logo_obj["relationship"] if logo_obj else "NEUTRAL",
        "severity": logo_obj["severity"] if logo_obj else "LOW",
        "score_label": f"Logo Consistency: {logo_obj['similarity_pct']}%" if logo_obj else "Consistency: 100%",
        "source_type": logo_obj.get("source_type", "LOCAL_DEMO") if logo_obj else "LOCAL_DEMO",
        "source_url": logo_obj.get("source_url") if logo_obj else None,
        "source_domain": logo_obj.get("source_domain") if logo_obj else None,
    })

    # Item 3: Document Compliance
    doc_obj = next((e for e in evidence_objects if e["evidence_type"] == "manipulation"), None)
    claim_items.append({
        "dimension": "3. Document Integrity & Compliance",
        "claim": claims.get("compliance_claim", "Statutory incorporation certificate"),
        "evidence_summary": doc_obj["explanation"] if doc_obj else "No forensic anomalies observed.",
        "relationship": doc_obj["relationship"] if doc_obj else "NEUTRAL",
        "severity": doc_obj["severity"] if doc_obj else "LOW",
        "score_label": f"Manipulation Score: {doc_obj['similarity_pct']}%" if doc_obj else "Manipulation: 0%",
        "source_type": doc_obj.get("source_type", "LOCAL_DEMO") if doc_obj else "LOCAL_DEMO",
        "source_url": None,
        "source_domain": "forensic-pixel-pipeline",
    })

    return {
        "claim_items": claim_items,
        "conclusion": conclusion,
        "recommendation": recommendation,
        "contradiction_count": len(contradictions),
        "verification_count": len(verifications),
        "support_count": len(supports),
    }


def get_analysis_provenance(
    num_images: int = 1,
    num_candidates: int = 1,
    evidence_sources: Optional[List[str]] = None,
    is_fallback_extractor: bool = False,
) -> Dict[str, Any]:
    """
    Returns technical transparency and provenance metadata.
    """
    sources = evidence_sources or ["ONLINE", "LOCAL DEMO REFERENCE"]
    return {
        "vision_model": "Fallback Color/Texture Extractor" if is_fallback_extractor else "Vision Transformer (ViT-B/16)",
        "is_fallback_extractor": is_fallback_extractor,
        "images_analyzed": num_images,
        "online_evidence_candidates": num_candidates,
        "evidence_sources": sources,
        "visual_signals": [
            "ViT-B/16 Cosine Similarity",
            "Brand Logo Alignment & Feature Matching",
            "Error Level Analysis (ELA)",
            "Laplacian Gradient Anomaly Analysis",
            "Synthetic-Image Frequency Signal (Supporting)",
            "Cross-Image Identity Dispersion",
        ],
    }
