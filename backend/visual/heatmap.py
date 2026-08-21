"""
heatmap.py — Explainable Visual Forensic Heatmap Generator.
Generates an overlay of localized anomaly signals (ELA, gradient noise,
compression discrepancies) onto the original image using OpenCV.
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image
from typing import Union, List, Tuple, Optional


def generate_forensic_heatmap(
    image: Union[Image.Image, np.ndarray, str],
    ela_image: Optional[np.ndarray] = None,
    gradient_map: Optional[np.ndarray] = None,
    suspicious_boxes: Optional[List[Tuple[int, int, int, int]]] = None,
    alpha: float = 0.45,
) -> np.ndarray:
    """
    Produce a heatmap overlay on top of the original image showing suspicious visual areas.

    Parameters
    ----------
    image : PIL.Image, numpy array (RGB/BGR), or file path
    ela_image : RGB image from compute_ela
    gradient_map : Grayscale map from compute_gradient_noise_anomaly
    suspicious_boxes : List of (x, y, w, h) bounding boxes
    alpha : Opacity of the colored heatmap overlay (0.0 to 1.0)

    Returns
    -------
    np.ndarray : RGB image with heatmap overlay and bounding box annotations
    """
    if isinstance(image, str):
        cv_bgr = cv2.imread(image)
    elif isinstance(image, Image.Image):
        cv_bgr = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    else:
        # Assume RGB or BGR numpy array
        if len(image.shape) == 3 and image.shape[2] == 3:
            cv_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            cv_bgr = image

    h, w = cv_bgr.shape[:2]

    # Combine signals into a single anomaly density map
    combined_map = np.zeros((h, w), dtype=np.float32)

    if ela_image is not None:
        ela_resized = cv2.resize(ela_image, (w, h))
        ela_gray = cv2.cvtColor(ela_resized, cv2.COLOR_RGB2GRAY).astype(np.float32)
        combined_map += ela_gray * 0.6

    if gradient_map is not None:
        grad_resized = cv2.resize(gradient_map, (w, h)).astype(np.float32)
        combined_map += grad_resized * 0.4

    if ela_image is None and gradient_map is None:
        # Fallback to direct local edge difference
        gray = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2GRAY)
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        combined_map = cv2.normalize(np.abs(lap), None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U).astype(np.float32)

    # Normalize to 0 - 255
    norm_anomaly = cv2.normalize(combined_map, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # Smooth the anomaly map for aesthetic risk heat representation
    blurred_anomaly = cv2.GaussianBlur(norm_anomaly, (21, 21), 0)

    # Apply Jet / Turbo colormap
    heatmap_colored = cv2.applyColorMap(blurred_anomaly, cv2.COLORMAP_JET)

    # Blend overlay with original image
    overlay = cv2.addWeighted(cv_bgr, 1.0 - alpha, heatmap_colored, alpha, 0)

    # Draw indicator boxes and labels if present
    if suspicious_boxes:
        for (bx, by, bw, bh) in suspicious_boxes:
            # Draw glowing bounding box
            cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), (0, 0, 255), 2)
            cv2.rectangle(overlay, (bx - 1, by - 1), (bx + bw + 1, by + bh + 1), (255, 255, 255), 1)

            # Label badge
            label = "Anomaly Indicator"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(overlay, (bx, max(0, by - th - 6)), (bx + tw + 6, max(th + 6, by)), (0, 0, 220), -1)
            cv2.putText(
                overlay,
                label,
                (bx + 3, max(th + 1, by - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

    # Convert back to RGB for PIL / Streamlit
    overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
    return overlay_rgb
