"""
manipulation.py — Image Forensics & Manipulation Detection Signal.
Implements Error Level Analysis (ELA), local noise variance analysis,
frequency inconsistencies, and optional synthetic-image suspicion indicators.
Never claims proof of fraud or tampering; reports indicators objectively.
"""

from __future__ import annotations

import io
import os
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
import cv2


def compute_ela(image: Image.Image, quality: int = 90, scale: int = 20) -> Tuple[np.ndarray, float]:
    """
    Perform Error Level Analysis (ELA) on an image.
    Recompresses image at a fixed JPEG quality, calculates pixel-by-pixel difference.
    
    Returns
    -------
    ela_diff_arr : np.ndarray (H, W, 3) visual ELA representation
    disparity_score : float normalized score of localized recompression variance
    """
    img_rgb = image.convert("RGB")
    
    # Save to in-memory JPEG buffer
    buf = io.BytesIO()
    img_rgb.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")
    
    # Compute absolute difference
    diff = ImageChops.difference(img_rgb, recompressed)
    
    # Enhance difference for visual analysis
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema]) if extrema else 1
    if max_diff == 0:
        max_diff = 1
    scale_factor = 255.0 / max_diff
    enhanced = ImageEnhance.Brightness(diff).enhance(min(scale_factor, scale))
    
    diff_arr = np.array(diff, dtype=np.float32)
    enhanced_arr = np.array(enhanced, dtype=np.uint8)
    
    # Calculate energy variance across grid blocks
    # High standard deviation between block differences indicates localized splicing / editing
    h, w, _ = diff_arr.shape
    block_size = max(16, min(h, w) // 16)
    
    block_energies = []
    for y in range(0, h - block_size + 1, block_size):
        for x in range(0, w - block_size + 1, block_size):
            patch = diff_arr[y : y + block_size, x : x + block_size]
            block_energies.append(np.mean(patch))
            
    if block_energies:
        std_energy = float(np.std(block_energies))
        max_energy = float(np.max(block_energies))
        mean_energy = float(np.mean(block_energies)) + 1e-4
        # Anomaly metric: high local disparity and peak-to-mean disparity
        disparity_score = (std_energy / mean_energy) * 35.0 + (max_energy / mean_energy) * 8.0
    else:
        disparity_score = 0.0
        
    return enhanced_arr, float(np.clip(disparity_score, 0.0, 100.0))


def compute_gradient_noise_anomaly(image_cv: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Analyze Laplacian local gradient variance to detect spliced sharp text or visual overlays
    on softer or resampled backgrounds.
    """
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    laplacian_abs = np.abs(laplacian)
    
    # Compute local standard deviation filter
    ksize = 15
    mean = cv2.blur(laplacian_abs, (ksize, ksize))
    mean_sq = cv2.blur(laplacian_abs ** 2, (ksize, ksize))
    variance = np.maximum(0, mean_sq - mean ** 2)
    local_std = np.sqrt(variance)
    
    # Normalize map
    norm_map = cv2.normalize(local_std, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    
    # Measure presence of localized extreme peaks (spliced overlays)
    high_threshold = np.percentile(local_std, 95)
    peak_ratio = np.sum(local_std > high_threshold * 1.3) / (local_std.size + 1e-6)
    anomaly_score = float(np.clip(peak_ratio * 3500.0, 0.0, 100.0))
    
    return norm_map, anomaly_score


def estimate_synthetic_suspicion(image_cv: np.ndarray) -> Tuple[float, str]:
    """
    Optional supporting signal for synthetic / AI-generated image artifacts.
    Evaluates color saturation distribution, spectral high-frequency decay,
    and ultra-smooth skin/texture surfaces.
    Never asserts certainty; reports only suspicion indicator.
    """
    hsv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    high_sat_ratio = np.mean(sat > 180)
    
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    dft = cv2.dft(np.float32(gray), flags=cv2.DFT_COMPLEX_OUTPUT)
    dft_shift = np.fft.fftshift(dft)
    magnitude_spectrum = 20 * np.log(cv2.magnitude(dft_shift[:, :, 0], dft_shift[:, :, 1]) + 1)
    
    h, w = gray.shape
    crow, ccol = h // 2, w // 2
    r_inner = min(h, w) // 8
    r_outer = min(h, w) // 4
    
    y, x = np.ogrid[:h, :w]
    mask_inner = ((x - ccol) ** 2 + (y - crow) ** 2) <= r_inner ** 2
    mask_outer = (((x - ccol) ** 2 + (y - crow) ** 2) <= r_outer ** 2) & (~mask_inner)
    
    inner_energy = np.mean(magnitude_spectrum[mask_inner]) if np.any(mask_inner) else 1.0
    outer_energy = np.mean(magnitude_spectrum[mask_outer]) if np.any(mask_outer) else 1.0
    
    ratio = outer_energy / (inner_energy + 1e-5)
    
    score = 0.0
    if ratio < 0.45 and high_sat_ratio > 0.30:
        score = 65.0 + (0.45 - ratio) * 100.0
    elif ratio < 0.50:
        score = 40.0 + (0.50 - ratio) * 80.0
    else:
        score = float(np.clip(high_sat_ratio * 40.0, 5.0, 35.0))
        
    score = float(np.clip(score, 5.0, 88.0))
    
    if score >= 60.0:
        desc = "Elevated synthetic/AI-generation visual markers detected (spectral and chromatic smoothness)."
    elif score >= 35.0:
        desc = "Moderate synthetic characteristics observed; within natural variance."
    else:
        desc = "Natural photographic frequency and chromatic signatures observed."
        
    return round(score, 1), desc


def analyze_image_manipulation(image: Union[Image.Image, str, np.ndarray]) -> Dict:
    """
    Perform forensic analysis on image to extract manipulation and synthetic indicators.
    
    Returns
    -------
    dict with keys:
        manipulation_score: float (0-100)
        risk_level: 'HIGH' | 'MEDIUM' | 'LOW'
        ela_image: np.ndarray (RGB)
        gradient_map: np.ndarray (Grayscale)
        synthetic_score: float (0-100)
        synthetic_desc: str
        suspicious_regions: list of bounding boxes (x, y, w, h)
        explanation: str
    """
    if isinstance(image, str):
        pil_img = Image.open(image).convert("RGB")
        cv_img = cv2.imread(image)
        if cv_img is None:
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    elif isinstance(image, Image.Image):
        pil_img = image.convert("RGB")
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    else:
        cv_img = image
        pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
    # 1. ELA
    ela_enhanced, ela_score = compute_ela(pil_img)
    
    # 2. Gradient anomaly
    grad_map, grad_score = compute_gradient_noise_anomaly(cv_img)
    
    # 3. Synthetic signal
    synth_score, synth_desc = estimate_synthetic_suspicion(cv_img)
    
    # 4. Detect localized suspicious bounding boxes from thresholded ELA / gradient
    gray_ela = cv2.cvtColor(ela_enhanced, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray_ela, 110, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    h, w, _ = cv_img.shape
    suspicious_boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > (h * w * 0.003) and area < (h * w * 0.50):
            bx, by, bw, bh = cv2.boundingRect(cnt)
            suspicious_boxes.append((int(bx), int(by), int(bw), int(bh)))
            
    # Composite manipulation score
    raw_manipulation = 0.55 * ela_score + 0.45 * grad_score
    
    # Boost score if multiple concentrated suspicious boxes found
    if len(suspicious_boxes) >= 2:
        raw_manipulation += 20.0
    elif len(suspicious_boxes) == 1:
        raw_manipulation += 10.0
        
    manipulation_score = round(float(np.clip(raw_manipulation, 0.0, 100.0)), 1)
    
    if manipulation_score >= 60.0:
        risk_level = "HIGH"
        explanation = (
            f"Manipulation indicators detected (Score: {manipulation_score}%). "
            f"High localized compression variance and edge-frequency anomalies observed."
        )
    elif manipulation_score >= 35.0:
        risk_level = "MEDIUM"
        explanation = (
            f"Moderate forensic anomalies detected (Score: {manipulation_score}%). "
            f"Minor compression artifacts or multi-layer graphics detected."
        )
    else:
        risk_level = "LOW"
        explanation = (
            f"Uniform compression and natural pixel distributions observed (Score: {manipulation_score}%)."
        )
        
    return {
        "manipulation_score": manipulation_score,
        "risk_level": risk_level,
        "ela_image": ela_enhanced,
        "gradient_map": grad_map,
        "synthetic_score": synth_score,
        "synthetic_desc": synth_desc,
        "suspicious_regions": suspicious_boxes,
        "explanation": explanation,
    }
