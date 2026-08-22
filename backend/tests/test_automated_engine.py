"""
backend/tests/test_automated_engine.py — Comprehensive Test Suite.
Tests:
- SSRF protection & IP blocking
- Asynchronous job lifecycle & state transitions
- Evidence safety rules (marketplace reuse capped, multi-signal corroboration for HIGH risk)
- Logo verification unavailable state
- Heatmap generation isolated strictly to manipulation
- Live vs demo mode badge reporting
- API endpoints & WebSocket progress streaming
"""

import sys
import unittest
import asyncio
from pathlib import Path
from PIL import Image
import numpy as np

# Ensure backend root on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from crawler.ssrf_validator import validate_url_security, is_ip_blocked
from services.evidence_normalizer import normalize_web_detection_evidence, is_marketplace_domain
from services.verified_brand_resolver import resolve_verified_brand_logo
from services.logo_detector import verify_merchant_logo
from services.forensic_heatmap import run_forensic_tampering_analysis
from services.visual_risk_scorer import calculate_visual_risk
from services.web_image_search import search_image_web_detection, get_vision_client
from api.job_manager import JobManager, get_job, get_job_report
from fastapi.testclient import TestClient
from main import app


class TestSSRFValidator(unittest.TestCase):
    def test_blocks_localhost_and_private_ips(self):
        blocked_urls = [
            "http://127.0.0.1:8000/secret",
            "http://localhost:3000",
            "http://192.168.1.1/admin",
            "http://10.0.0.5/api",
            "http://172.16.0.1/status",
            "http://169.254.169.254/latest/meta-data/",
            "http://0.0.0.0:80",
        ]
        for url in blocked_urls:
            is_valid, ip, err = validate_url_security(url)
            self.assertFalse(is_valid, f"Expected {url} to be blocked by SSRF validator.")

    def test_permits_public_domains(self):
        public_url = "https://example.com"
        is_valid, ip, err = validate_url_security(public_url)
        self.assertTrue(is_valid, f"Expected {public_url} to be valid: {err}")


class TestEvidenceSafetyAndScoring(unittest.TestCase):
    def test_marketplace_only_reuse_cannot_cause_high_risk(self):
        # A single marketplace match on Amazon should be capped at REVIEW (score <= 60), not HIGH (>=70)
        marketplace_evidence = [
            {
                "asset_url": "https://example.com/product.jpg",
                "asset_type": "product_image",
                "signal_type": "external_image_reuse",
                "score": 65,
                "is_marketplace_only": True,
                "is_stock_only": False,
                "matched_pages": [{"url": "https://www.amazon.com/dp/B123", "domain": "amazon.com"}],
                "matched_images": ["https://images-na.ssl-images-amazon.com/test.jpg"],
                "explanation": "Visual reuse observed across external marketplace",
                "heatmap_url": None,
            }
        ]
        score, risk_level, action = calculate_visual_risk(marketplace_evidence, brand_verification_status="UNAVAILABLE")
        self.assertLess(score, 70, "Marketplace match alone should not produce score >= 70.")
        self.assertNotEqual(risk_level, "HIGH", "Marketplace match alone should not result in HIGH risk.")
        self.assertNotEqual(action, "MANUAL_REVIEW")

    def test_corroborating_signals_produce_high_risk(self):
        # Image reuse + Verified Logo mismatch should trigger HIGH risk and MANUAL_REVIEW
        corroborated_evidence = [
            {
                "asset_url": "https://example.com/product.jpg",
                "asset_type": "product_image",
                "signal_type": "external_image_reuse",
                "score": 80,
                "is_marketplace_only": False,
                "matched_pages": [{"url": "https://rogue-catalog.com/item", "domain": "rogue-catalog.com"}],
                "matched_images": ["https://rogue-catalog.com/img.jpg"],
                "explanation": "Stolen catalog reuse",
                "heatmap_url": None,
            },
            {
                "asset_url": "https://example.com/logo.jpg",
                "asset_type": "logo",
                "signal_type": "potential_logo_mismatch",
                "score": 85,
                "matched_pages": [],
                "matched_images": [],
                "explanation": "Divergent logo from verified brand registry",
                "heatmap_url": None,
            },
        ]
        score, risk_level, action = calculate_visual_risk(corroborated_evidence, brand_verification_status="VERIFIED")
        self.assertGreaterEqual(score, 70, f"Expected corroborated score >= 70, got {score}")
        self.assertEqual(risk_level, "HIGH")
        self.assertEqual(action, "MANUAL_REVIEW")

    def test_never_auto_rejects(self):
        # Even with high tampering, the recommendation must be MANUAL_REVIEW, never REJECT
        tampered_evidence = [
            {
                "asset_url": "https://example.com/cert.jpg",
                "asset_type": "certificate",
                "signal_type": "manipulation",
                "score": 90,
                "matched_pages": [],
                "matched_images": [],
                "explanation": "Severe tampering anomalies",
                "heatmap_url": "data:image/png;base64,sample",
            }
        ]
        score, risk_level, action = calculate_visual_risk(tampered_evidence, brand_verification_status="UNAVAILABLE")
        self.assertEqual(action, "MANUAL_REVIEW")


class TestLogoVerification(unittest.TestCase):
    def test_logo_unavailable_when_brand_unknown(self):
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        status, evidence = verify_merchant_logo(img, "https://example.com/logo.png", claimed_brand=None)
        self.assertEqual(status, "UNAVAILABLE")
        self.assertIsNone(evidence)

    def test_logo_unavailable_for_unregistered_brand(self):
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        status, evidence = verify_merchant_logo(img, "https://example.com/logo.png", claimed_brand="CompletelyUnregisteredBrand12345")
        self.assertEqual(status, "UNAVAILABLE")
        self.assertIsNone(evidence)


class TestHeatmapRules(unittest.TestCase):
    def test_heatmap_only_for_manipulation(self):
        # Normalized reuse evidence should have heatmap_url = None
        fake_item = {
            "meta": {"src": "https://example.com/p1.jpg", "asset_type": "product_image"},
            "web_detection": {
                "full_matching_images": ["https://amazon.com/p1.jpg"],
                "partial_matching_images": [],
                "pages_with_matching_images": [{"url": "https://amazon.com/dp/1", "page_title": "Amazon"}],
            }
        }
        norm = normalize_web_detection_evidence(fake_item, merchant_domain="example.com")
        self.assertIsNone(norm["heatmap_url"], "Heatmap URL must be None for image reuse.")


class TestAsyncAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_post_analyse_merchant_returns_queued_job(self):
        response = self.client.post(
            "/api/analyse-merchant",
            json={
                "merchant_id": "test_merchant_001",
                "website_url": "https://example.com",
                "claimed_brand": "Example Brand",
                "merchant_category": "electronics",
            }
        )
        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertIn("job_id", data)
        self.assertEqual(data["status"], "QUEUED")

        job_id = data["job_id"]
        # Poll job status
        status_res = self.client.get(f"/api/analysis-jobs/{job_id}")
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.json()["job_id"], job_id)

    def test_post_analyse_merchant_rejects_ssrf(self):
        response = self.client.post(
            "/api/analyse-merchant",
            json={
                "merchant_id": "bad_merchant",
                "website_url": "http://127.0.0.1:8000/internal",
            }
        )
        self.assertEqual(response.status_code, 400)


class TestWebSocketsAndModes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_demo_mode_badge_when_no_credentials(self):
        client, mode = get_vision_client()
        self.assertIn(mode, ["SIMULATED_DEMO_MODE", "LIVE_WEB_DETECTION"])

    def test_websocket_connection_and_streaming(self):
        # Create a test job
        job_id = JobManager.create_job(
            merchant_id="ws_test_merchant",
            website_url="https://example.com",
            claimed_brand="Example Brand",
        )
        with self.client.websocket_connect(f"/ws/analysis/{job_id}") as ws:
            first_msg = ws.receive_json()
            self.assertIn("status", first_msg)
            self.assertIn("message", first_msg)
            self.assertEqual(first_msg["job_id"], job_id)


if __name__ == "__main__":
    unittest.main()
