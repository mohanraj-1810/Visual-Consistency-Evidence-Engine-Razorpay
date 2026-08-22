"""
services/web_image_search.py — Google Cloud Vision Web Detection Client.
Queries Google Cloud Vision Web Detection API for matching images, web entities,
and referring web pages. Features SHA-256 image caching and automatic fallback
to SIMULATED_DEMO_MODE when credentials are not configured.
"""

from __future__ import annotations

import os
import io
import hashlib
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image

try:
    from google.cloud import vision
    from google.auth.exceptions import DefaultCredentialsError
    _VISION_AVAILABLE = True
except ImportError:
    _VISION_AVAILABLE = False


# In-memory SHA-256 image search cache to prevent redundant paid API calls
# sha256_hash -> cached_web_detection_result
_IMAGE_SEARCH_CACHE: Dict[str, Dict[str, Any]] = {}


def get_vision_client() -> Tuple[Optional[Any], str]:
    """
    Initializes Google Cloud Vision client if credentials exist.
    Returns (client, analysis_mode) where analysis_mode is:
      - 'LIVE_WEB_DETECTION'
      - 'SIMULATED_DEMO_MODE'
    """
    if not _VISION_AVAILABLE:
        return None, "SIMULATED_DEMO_MODE"

    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

    # If creds file path is specified, ensure it actually exists on disk
    if creds_path and not os.path.exists(creds_path):
        return None, "SIMULATED_DEMO_MODE"

    try:
        # If credentials or default environment exists
        if creds_path or project_id:
            client = vision.ImageAnnotatorClient()
            return client, "LIVE_WEB_DETECTION"
        else:
            return None, "SIMULATED_DEMO_MODE"
    except Exception:
        return None, "SIMULATED_DEMO_MODE"


def search_image_web_detection(
    image: Image.Image,
    sha256_hash: Optional[str] = None,
    client: Optional[Any] = None,
    mode: str = "SIMULATED_DEMO_MODE",
    asset_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Submits an image to Google Cloud Vision Web Detection (or simulated fallback)
    and returns parsed matches. Utilizes in-memory SHA-256 caching.
    """
    # 1. Compute hash if not provided
    if not sha256_hash:
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        raw_bytes = buf.getvalue()
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
    else:
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        raw_bytes = buf.getvalue()

    # 2. Check cache
    if sha256_hash in _IMAGE_SEARCH_CACHE:
        cached_result = dict(_IMAGE_SEARCH_CACHE[sha256_hash])
        cached_result["cached"] = True
        return cached_result

    # 3. Live Google Cloud Vision execution
    if mode == "LIVE_WEB_DETECTION" and client is not None:
        try:
            vision_image = vision.Image(content=raw_bytes)
            web_detection_params = vision.WebDetectionParams(include_geo_results=False)
            image_context = vision.ImageContext(web_detection_params=web_detection_params)

            response = client.web_detection(image=vision_image, image_context=image_context, timeout=12.0)
            web_detection = response.web_detection

            full_matches = [img.url for img in web_detection.full_matching_images if img.url]
            partial_matches = [img.url for img in web_detection.partial_matching_images if img.url]
            visually_similar = [img.url for img in web_detection.visually_similar_images if img.url]
            
            web_entities = [
                {"description": entity.description, "score": round(float(entity.score), 4), "entity_id": entity.entity_id}
                for entity in web_detection.web_entities if entity.description
            ]

            pages_with_matches = []
            for page in web_detection.pages_with_matching_images:
                pages_with_matches.append({
                    "url": page.url,
                    "page_title": page.page_title,
                    "full_matching_images": [img.url for img in page.full_matching_images if img.url],
                    "partial_matching_images": [img.url for img in page.partial_matching_images if img.url],
                })

            result = {
                "sha256": sha256_hash,
                "analysis_mode": "LIVE_WEB_DETECTION",
                "full_matching_images": full_matches,
                "partial_matching_images": partial_matches,
                "visually_similar_images": visually_similar,
                "web_entities": web_entities,
                "pages_with_matching_images": pages_with_matches,
                "cached": False,
            }
            _IMAGE_SEARCH_CACHE[sha256_hash] = result
            return result
        except Exception as e:
            # Fall back gracefully to simulation if API call fails
            mode = "SIMULATED_DEMO_MODE"

    # 4. Fallback: Simulated Demo Mode
    sim_result = _simulate_web_detection(image, sha256_hash, asset_hint)
    _IMAGE_SEARCH_CACHE[sha256_hash] = sim_result
    return sim_result


def _simulate_web_detection(image: Image.Image, sha256_hash: str, asset_hint: Optional[str] = None) -> Dict[str, Any]:
    """Generates an honest simulated web detection result when operating in demo mode."""
    # Deterministic simulation based on hash and hint
    is_suspicious = bool(asset_hint and any(kw in asset_hint.lower() for kw in ["stolen", "stock", "fake", "luxury", "omega", "nike", "copy"]))

    if is_suspicious:
        full_matches = ["https://images-na.ssl-images-amazon.com/images/I/71example.jpg"]
        partial_matches = ["https://ae01.alicdn.com/kf/Sexample.jpg"]
        pages = [
            {
                "url": "https://www.amazon.com/dp/B08EXAMPLE",
                "page_title": "Original Product Listing on Amazon Marketplace",
                "full_matching_images": ["https://images-na.ssl-images-amazon.com/images/I/71example.jpg"],
                "partial_matching_images": [],
            }
        ]
        entities = [
            {"description": "E-Commerce Catalog", "score": 0.89, "entity_id": "/m/01"},
            {"description": "Product Photography", "score": 0.84, "entity_id": "/m/02"},
        ]
    else:
        full_matches = []
        partial_matches = []
        pages = []
        entities = [
            {"description": "Merchant Visual", "score": 0.72, "entity_id": "/m/03"}
        ]

    return {
        "sha256": sha256_hash,
        "analysis_mode": "SIMULATED_DEMO_MODE",
        "full_matching_images": full_matches,
        "partial_matching_images": partial_matches,
        "visually_similar_images": [],
        "web_entities": entities,
        "pages_with_matching_images": pages,
        "cached": False,
    }


async def batch_search_images(
    images_with_meta: List[Tuple[Image.Image, Dict[str, Any]]],
    client: Optional[Any] = None,
    mode: str = "SIMULATED_DEMO_MODE",
) -> List[Dict[str, Any]]:
    """
    Executes web image detection across a batch of extracted assets asynchronously.
    """
    loop = asyncio.get_running_loop()
    tasks = []

    for img, meta in images_with_meta:
        sha256_hash = meta.get("sha256")
        hint = meta.get("alt") or meta.get("title") or meta.get("search_query_hint")
        task = loop.run_in_executor(
            None,
            search_image_web_detection,
            img,
            sha256_hash,
            client,
            mode,
            hint,
        )
        tasks.append((task, meta, img))

    results = []
    for task, meta, img in tasks:
        try:
            web_res = await task
            results.append({
                "meta": meta,
                "image": img,
                "web_detection": web_res,
            })
        except Exception:
            continue

    return results
