"""
services/forensic_heatmap.py — Forensic Manipulation and Tampering Heatmaps.
Generates explainable heatmaps ONLY for image manipulation and digital tampering
(Error Level Analysis & Laplacian Gradient High-Frequency Noise).
Strictly does NOT generate fake heatmaps for standard image reuse.
"""

from __future__ import annotations

import io
import base64
from typing import Dict, List, Optional, Any, Tuple
import cv2
import numpy as np
from PIL import Image

from visual.manipulation import analyze_image_manipulation
from visual.heatmap import generate_forensic_heatmap


def image_to_base64_url(img: Any, fmt: str = "PNG") -> Optional[str]:
    """Converts a PIL Image or numpy RGB image to a Base64 data URL."""
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
            elif img.shape[2] == 4:
                pil_img = Image.fromarray(img, mode="RGBA")
            else:
                return None
        elif isinstance(img, Image.Image):
            pil_img = img
        else:
            return None

        buf = io.BytesIO()
        pil_img.save(buf, format=fmt)
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/{fmt.lower()};base64,{encoded}"
    except Exception:
        return None


def run_forensic_tampering_analysis(
    target_image: Optional[Image.Image],
    asset_url: Optional[str],
    asset_type: str = "certificate",
) -> Tuple[int, Optional[Dict[str, Any]]]:
    """
    Executes forensic compression and edge anomaly checks on suspicious documents/assets.
    Returns (manipulation_score, evidence_object).
    """
    if target_image is None:
        return 0, None

    try:
        manip_data = analyze_image_manipulation(target_image)
        score = int(round(manip_data.get("manipulation_score", 0.0)))
        
        heatmap_overlay = generate_forensic_heatmap(
            target_image,
            ela_image=manip_data.get("ela_image"),
            gradient_map=manip_data.get("gradient_map"),
            suspicious_boxes=manip_data.get("suspicious_regions", []),
        )
        heatmap_b64 = image_to_base64_url(heatmap_overlay)

        if score >= 35:
            explanation = (
                f"Digital manipulation indicators detected in {asset_type} (forensic score: {score}/100). "
                f"Localized compression anomalies and high-frequency edge splicing identified."
            )
        else:
            explanation = f"No digital manipulation or splicing anomalies observed on {asset_type}."

        evidence = {
            "asset_url": asset_url or f"extracted_{asset_type}",
            "asset_type": asset_type,
            "signal_type": "manipulation",
            "score": score,
            "matched_pages": [],
            "matched_images": [],
            "explanation": explanation,
            "heatmap_url": heatmap_b64 if score >= 35 else None,
        }
        return score, evidence
    except Exception as e:
        return 0, {
            "asset_url": asset_url or f"extracted_{asset_type}",
            "asset_type": asset_type,
            "signal_type": "manipulation",
            "score": 0,
            "matched_pages": [],
            "matched_images": [],
            "explanation": f"Forensic scan notice: {str(e)}",
            "heatmap_url": None,
        }
