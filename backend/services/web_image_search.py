"""
services/web_image_search.py — Google Cloud Vision API Client & Intelligence Engine.
Supports:
  1. Google Cloud Vision REST API via API Key (GOOGLE_VISION_API_KEY / GOOGLE_API_KEY)
  2. Google Cloud SDK via Service Account (GOOGLE_APPLICATION_CREDENTIALS)
  3. Multi-feature annotations: WEB_DETECTION, LOGO_DETECTION, TEXT_DETECTION (OCR),
     LABEL_DETECTION, and SAFE_SEARCH_DETECTION.
  4. In-memory SHA-256 caching to prevent redundant billable API calls.
  5. Automatic resilient fallback to SIMULATED_DEMO_MODE on credential/billing errors.
"""

from __future__ import annotations

import os
import io
import base64
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from PIL import Image
import requests

# ── 1. Automatic .env Loader ───────────────────────────────────────────────────
def _load_env_files():
    """Lightweight built-in loader for .env files without requiring external packages."""
    env_paths = [
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path.cwd() / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists() and env_path.is_file():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
            except Exception:
                pass

_load_env_files()

# Optional Google Cloud SDK import
try:
    from google.cloud import vision
    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False


# In-memory SHA-256 image search cache to prevent redundant paid API calls
# sha256_hash -> cached_annotation_result
_IMAGE_SEARCH_CACHE: Dict[str, Dict[str, Any]] = {}
_VISION_API_ENDPOINT = "https://vision.googleapis.com/v1/images:annotate"


def get_vision_api_key() -> Optional[str]:
    """Retrieve Google Vision API key from environment or .env files."""
    _load_env_files()
    key = os.environ.get("GOOGLE_VISION_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key and key.strip():
        return key.strip()
    return None


def get_vision_client() -> Tuple[Optional[Any], str]:
    """
    Initializes Google Cloud Vision client (API Key or Service Account).
    Returns (client_or_config, analysis_mode) where analysis_mode is:
      - 'LIVE_WEB_DETECTION'
      - 'SIMULATED_DEMO_MODE'
    """
    # 1. Check API Key
    api_key = get_vision_api_key()
    if api_key:
        return {"api_key": api_key, "type": "REST_API_KEY"}, "LIVE_WEB_DETECTION"

    # 2. Check Service Account SDK
    if _SDK_AVAILABLE:
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if creds_path and os.path.exists(creds_path):
            try:
                client = vision.ImageAnnotatorClient()
                return client, "LIVE_WEB_DETECTION"
            except Exception:
                pass
        elif project_id:
            try:
                client = vision.ImageAnnotatorClient()
                return client, "LIVE_WEB_DETECTION"
            except Exception:
                pass

    return None, "SIMULATED_DEMO_MODE"


def get_vision_status() -> Dict[str, Any]:
    """Diagnostic helper reporting active Google Vision configuration and status."""
    client_or_cfg, mode = get_vision_client()
    api_key = get_vision_api_key()
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key and len(api_key) > 12 else ("SET" if api_key else "NOT_CONFIGURED")
    
    return {
        "analysis_mode": mode,
        "api_key_configured": bool(api_key),
        "api_key_masked": masked_key,
        "sdk_available": _SDK_AVAILABLE,
        "service_account_configured": bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")),
        "cached_images_count": len(_IMAGE_SEARCH_CACHE),
    }


def _call_vision_rest_api(
    raw_bytes: bytes,
    api_key: str,
    features: Optional[List[str]] = None,
    timeout: float = 10.0,
) -> Optional[Dict[str, Any]]:
    """
    Executes a direct REST call to Google Cloud Vision API v1 endpoint.
    """
    if not features:
        features = ["WEB_DETECTION", "LOGO_DETECTION", "TEXT_DETECTION", "LABEL_DETECTION", "SAFE_SEARCH_DETECTION"]

    feature_requests = [{"type": feat, "maxResults": 10} for feat in features]
    encoded_image = base64.b64encode(raw_bytes).decode("utf-8")

    payload = {
        "requests": [
            {
                "image": {"content": encoded_image},
                "features": feature_requests,
            }
        ]
    }

    try:
        url = f"{_VISION_API_ENDPOINT}?key={api_key}"
        resp = requests.post(url, json=payload, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            responses = data.get("responses", [])
            if responses:
                first_resp = responses[0]
                if "error" in first_resp:
                    # Vision item level error (e.g. billing or quota)
                    err_msg = first_resp["error"].get("message", "")
                    print(f"[GOOGLE_VISION_API] Item notice: {err_msg}")
                    return None
                return first_resp
        else:
            err_text = resp.text[:250]
            print(f"[GOOGLE_VISION_API] HTTP {resp.status_code}: {err_text}")
            return None
    except Exception as e:
        print(f"[GOOGLE_VISION_API] Request exception: {e}")
        return None


def annotate_image_vision(
    image: Image.Image,
    sha256_hash: Optional[str] = None,
    client: Optional[Any] = None,
    mode: str = "SIMULATED_DEMO_MODE",
    asset_hint: Optional[str] = None,
    features: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Annotates an image using Google Cloud Vision (REST API or SDK), with SHA-256 caching
    and graceful fallback to simulated demo mode.
    
    Returns structured visual intelligence:
      - web_detection (matches, pages, entities, best guess)
      - logos (detected brand logos and bounding boxes)
      - text_ocr (detected text on the image)
      - labels (product & visual categories)
      - safe_search (content moderation)
    """
    # 1. Compute hash and raw bytes
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    raw_bytes = buf.getvalue()
    if not sha256_hash:
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

    # 2. Check cache
    if sha256_hash in _IMAGE_SEARCH_CACHE:
        cached_result = dict(_IMAGE_SEARCH_CACHE[sha256_hash])
        cached_result["cached"] = True
        return cached_result

    # 3. Live Google Cloud Vision Execution
    if client is None and mode == "SIMULATED_DEMO_MODE":
        # Check if client was not passed but environment has credentials
        client, detected_mode = get_vision_client()
        if detected_mode == "LIVE_WEB_DETECTION":
            mode = "LIVE_WEB_DETECTION"

    if mode == "LIVE_WEB_DETECTION" and client is not None:
        # A. REST API Key Client
        if isinstance(client, dict) and client.get("type") == "REST_API_KEY":
            api_key = client.get("api_key")
            api_resp = _call_vision_rest_api(raw_bytes, api_key, features=features)
            if api_resp:
                result = _parse_rest_vision_response(api_resp, sha256_hash)
                _IMAGE_SEARCH_CACHE[sha256_hash] = result
                return result
            else:
                # If API call failed (e.g. billing not enabled on key), fallback gracefully
                mode = "SIMULATED_DEMO_MODE"

        # B. Native Google Cloud SDK Client
        elif _SDK_AVAILABLE and hasattr(client, "web_detection"):
            try:
                vision_image = vision.Image(content=raw_bytes)
                web_params = vision.WebDetectionParams(include_geo_results=False)
                img_ctx = vision.ImageContext(web_detection_params=web_params)
                
                resp = client.web_detection(image=vision_image, image_context=img_ctx, timeout=12.0)
                wd = resp.web_detection

                full_matches = [img.url for img in wd.full_matching_images if img.url]
                partial_matches = [img.url for img in wd.partial_matching_images if img.url]
                visually_similar = [img.url for img in wd.visually_similar_images if img.url]
                entities = [
                    {"description": e.description, "score": round(float(e.score), 4), "entity_id": e.entity_id}
                    for e in wd.web_entities if e.description
                ]
                pages = [
                    {
                        "url": p.url,
                        "page_title": p.page_title,
                        "full_matching_images": [img.url for img in p.full_matching_images if img.url],
                        "partial_matching_images": [img.url for img in p.partial_matching_images if img.url],
                    }
                    for p in wd.pages_with_matching_images
                ]

                result = {
                    "sha256": sha256_hash,
                    "analysis_mode": "LIVE_WEB_DETECTION",
                    "full_matching_images": full_matches,
                    "partial_matching_images": partial_matches,
                    "visually_similar_images": visually_similar,
                    "web_entities": entities,
                    "pages_with_matching_images": pages,
                    "logos": [],
                    "ocr_text": "",
                    "labels": [],
                    "safe_search": {},
                    "cached": False,
                }
                _IMAGE_SEARCH_CACHE[sha256_hash] = result
                return result
            except Exception as e:
                print(f"[GOOGLE_VISION_SDK] SDK exception: {e}")
                mode = "SIMULATED_DEMO_MODE"

    # 4. Fallback: Honest Simulated Demo Mode
    sim_result = _simulate_web_detection(image, sha256_hash, asset_hint)
    _IMAGE_SEARCH_CACHE[sha256_hash] = sim_result
    return sim_result


def _parse_rest_vision_response(api_resp: Dict[str, Any], sha256_hash: str) -> Dict[str, Any]:
    """Parses Google Cloud Vision REST response into standardized schema."""
    wd = api_resp.get("webDetection", {})
    full_matches = [img.get("url") for img in wd.get("fullMatchingImages", []) if img.get("url")]
    partial_matches = [img.get("url") for img in wd.get("partialMatchingImages", []) if img.get("url")]
    visually_similar = [img.get("url") for img in wd.get("visuallySimilarImages", []) if img.get("url")]
    
    entities = [
        {
            "description": ent.get("description", ""),
            "score": round(float(ent.get("score", 0.0)), 4),
            "entity_id": ent.get("entityId", ""),
        }
        for ent in wd.get("webEntities", [])
        if ent.get("description")
    ]

    pages = []
    for page in wd.get("pagesWithMatchingImages", []):
        pages.append({
            "url": page.get("url", ""),
            "page_title": page.get("pageTitle", ""),
            "full_matching_images": [img.get("url") for img in page.get("fullMatchingImages", []) if img.get("url")],
            "partial_matching_images": [img.get("url") for img in page.get("partialMatchingImages", []) if img.get("url")],
        })

    # Logos
    logos = []
    for logo_ann in api_resp.get("logoAnnotations", []):
        desc = logo_ann.get("description")
        score = float(logo_ann.get("score", 0.0))
        if desc:
            logos.append({
                "brand_name": desc,
                "confidence": round(score, 4),
                "bounding_poly": logo_ann.get("boundingPoly", {}),
            })

    # OCR Text
    text_annotations = api_resp.get("textAnnotations", [])
    full_ocr_text = text_annotations[0].get("description", "") if text_annotations else ""

    # Labels
    labels = [
        {"description": lbl.get("description", ""), "score": round(float(lbl.get("score", 0.0)), 4)}
        for lbl in api_resp.get("labelAnnotations", [])
        if lbl.get("description")
    ]

    # Safe Search
    safe_search = api_resp.get("safeSearchAnnotation", {})

    return {
        "sha256": sha256_hash,
        "analysis_mode": "LIVE_WEB_DETECTION",
        "full_matching_images": full_matches,
        "partial_matching_images": partial_matches,
        "visually_similar_images": visually_similar,
        "web_entities": entities,
        "pages_with_matching_images": pages,
        "logos": logos,
        "ocr_text": full_ocr_text,
        "labels": labels,
        "safe_search": safe_search,
        "cached": False,
    }


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
    return annotate_image_vision(
        image=image,
        sha256_hash=sha256_hash,
        client=client,
        mode=mode,
        asset_hint=asset_hint,
    )


def _simulate_web_detection(image: Image.Image, sha256_hash: str, asset_hint: Optional[str] = None) -> Dict[str, Any]:
    """Generates an honest simulated web detection result when operating in demo mode."""
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
        logos = []
    else:
        full_matches = []
        partial_matches = []
        pages = []
        entities = [
            {"description": "Merchant Visual", "score": 0.72, "entity_id": "/m/03"}
        ]
        logos = []

    return {
        "sha256": sha256_hash,
        "analysis_mode": "SIMULATED_DEMO_MODE",
        "full_matching_images": full_matches,
        "partial_matching_images": partial_matches,
        "visually_similar_images": [],
        "web_entities": entities,
        "pages_with_matching_images": pages,
        "logos": logos,
        "ocr_text": "",
        "labels": [],
        "safe_search": {},
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
