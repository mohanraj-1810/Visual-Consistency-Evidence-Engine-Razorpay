"""
services/verified_brand_resolver.py — Resolves official verified brand logos from trusted registries.
If a claimed brand is missing or unverified, safely returns UNAVAILABLE status
to avoid false positive logo penalties.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Dict, Tuple, Any
from PIL import Image


# Path to local registered brand logo database
_BASE_DIR = Path(__file__).resolve().parent.parent
_LOGOS_DIR = _BASE_DIR / "dataset" / "logos"


def resolve_verified_brand_logo(claimed_brand: Optional[str]) -> Tuple[str, Optional[Image.Image], Optional[str]]:
    """
    Looks up official verified reference logo for a claimed brand.

    Returns
    -------
    (brand_verification_status, verified_logo_image, matched_brand_name)
    where brand_verification_status is 'VERIFIED' or 'UNAVAILABLE'.
    """
    if not claimed_brand or not isinstance(claimed_brand, str):
        return "UNAVAILABLE", None, None

    brand_norm = claimed_brand.strip().lower().replace("-", " ").replace("_", " ")
    if len(brand_norm) < 2:
        return "UNAVAILABLE", None, None

    if not _LOGOS_DIR.exists():
        return "UNAVAILABLE", None, None

    # Search known verified logos in repository
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    for f in _LOGOS_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in valid_exts:
            fname_clean = f.stem.lower().replace("-", " ").replace("_", " ")
            if brand_norm in fname_clean or fname_clean in brand_norm:
                try:
                    img = Image.open(str(f)).convert("RGB")
                    return "VERIFIED", img, f.stem
                except Exception:
                    continue

    return "UNAVAILABLE", None, None
