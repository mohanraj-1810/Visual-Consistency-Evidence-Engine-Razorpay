"""
backend/tests/test_google_vision.py — Unit Tests for Google Cloud Vision API Integration.
Verifies API Key loading, client initialization, REST annotation parser, SHA-256 caching,
multi-feature detection (Web, Logo, Text OCR, Labels), and fallback handling.
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image, ImageDraw

# Ensure backend root on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.web_image_search import (
    get_vision_api_key,
    get_vision_client,
    get_vision_status,
    search_image_web_detection,
    annotate_image_vision,
    _parse_rest_vision_response,
    _call_vision_rest_api,
    _IMAGE_SEARCH_CACHE,
)
from services.logo_detector import verify_merchant_logo


class TestGoogleVisionIntegration(unittest.TestCase):

    def setUp(self):
        # Create a sample test image
        self.img = Image.new("RGB", (100, 100), color="blue")
        draw = ImageDraw.Draw(self.img)
        draw.text((10, 10), "Test Brand", fill="white")

    def test_vision_api_key_loading(self):
        key = get_vision_api_key()
        self.assertIsNotNone(key, "Vision API key should be loaded from .env or environment")
        self.assertTrue(key.startswith("AIzaSy"), f"Key should match Google API key format, got: {key[:6]}")

    def test_vision_client_initialization_with_api_key(self):
        client_cfg, mode = get_vision_client()
        self.assertEqual(mode, "LIVE_WEB_DETECTION")
        self.assertIsInstance(client_cfg, dict)
        self.assertEqual(client_cfg.get("type"), "REST_API_KEY")
        self.assertIn("api_key", client_cfg)

    def test_vision_status_diagnostic(self):
        status = get_vision_status()
        self.assertEqual(status.get("analysis_mode"), "LIVE_WEB_DETECTION")
        self.assertTrue(status.get("api_key_configured"))
        self.assertTrue(status.get("api_key_masked").startswith("AIzaSy"))

    def test_parse_rest_vision_response(self):
        mock_api_resp = {
            "webDetection": {
                "fullMatchingImages": [{"url": "https://example.com/orig.jpg"}],
                "partialMatchingImages": [{"url": "https://example.com/part.jpg"}],
                "visuallySimilarImages": [{"url": "https://example.com/sim.jpg"}],
                "webEntities": [
                    {"description": "Nike Air Max", "score": 0.95, "entityId": "/m/0123"}
                ],
                "pagesWithMatchingImages": [
                    {
                        "url": "https://nike.com/product",
                        "pageTitle": "Nike Air Max Official Listing",
                        "fullMatchingImages": [{"url": "https://example.com/orig.jpg"}],
                        "partialMatchingImages": []
                    }
                ]
            },
            "logoAnnotations": [
                {
                    "description": "Nike",
                    "score": 0.98,
                    "boundingPoly": {"vertices": [{"x": 10, "y": 10}, {"x": 50, "y": 50}]}
                }
            ],
            "textAnnotations": [
                {"description": "JUST DO IT\nNIKE AIR"}
            ],
            "labelAnnotations": [
                {"description": "Sneakers", "score": 0.92},
                {"description": "Footwear", "score": 0.89}
            ],
            "safeSearchAnnotation": {
                "adult": "VERY_UNLIKELY",
                "spoof": "UNLIKELY"
            }
        }

        parsed = _parse_rest_vision_response(mock_api_resp, "test_hash_123")
        self.assertEqual(parsed["analysis_mode"], "LIVE_WEB_DETECTION")
        self.assertEqual(parsed["full_matching_images"], ["https://example.com/orig.jpg"])
        self.assertEqual(len(parsed["logos"]), 1)
        self.assertEqual(parsed["logos"][0]["brand_name"], "Nike")
        self.assertEqual(parsed["logos"][0]["confidence"], 0.98)
        self.assertEqual(parsed["ocr_text"], "JUST DO IT\nNIKE AIR")
        self.assertEqual(len(parsed["labels"]), 2)
        self.assertEqual(parsed["labels"][0]["description"], "Sneakers")

    def test_sha256_caching(self):
        dummy_hash = "custom_test_hash_cache_test"
        _IMAGE_SEARCH_CACHE[dummy_hash] = {
            "sha256": dummy_hash,
            "analysis_mode": "LIVE_WEB_DETECTION",
            "full_matching_images": ["https://cached.com/img.jpg"],
            "partial_matching_images": [],
            "visually_similar_images": [],
            "web_entities": [],
            "pages_with_matching_images": [],
            "logos": [],
            "ocr_text": "",
            "labels": [],
            "safe_search": {},
            "cached": False,
        }

        res = search_image_web_detection(self.img, sha256_hash=dummy_hash)
        self.assertTrue(res.get("cached"), "Cached result should flag cached=True")
        self.assertEqual(res.get("full_matching_images"), ["https://cached.com/img.jpg"])

    def test_logo_detector_corroboration_with_vision(self):
        detected_logos = [
            {"brand_name": "Nike", "confidence": 0.95}
        ]
        status, evidence = verify_merchant_logo(
            self.img,
            logo_url="https://merchant.com/logo.png",
            claimed_brand="Nike",
            detected_logos=detected_logos
        )
        # Should execute safely without error
        self.assertIn(status, ["VERIFIED", "UNAVAILABLE"])
        if evidence:
            self.assertIn("signal_type", evidence)

    def test_fallback_on_api_error(self):
        # Even if client fails or returns 403, annotate_image_vision should return valid schema
        client_cfg = {"api_key": "INVALID_OR_UNBILLED_KEY", "type": "REST_API_KEY"}
        res = annotate_image_vision(
            self.img,
            client=client_cfg,
            mode="LIVE_WEB_DETECTION",
            asset_hint="luxury watch stolen",
        )
        self.assertIsNotNone(res)
        self.assertIn("full_matching_images", res)
        self.assertIn("web_entities", res)
        self.assertIn("analysis_mode", res)


if __name__ == "__main__":
    unittest.main()
