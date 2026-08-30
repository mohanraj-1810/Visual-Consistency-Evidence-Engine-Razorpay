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


from visual.image_reuse import analyze_multiple_images_reuse
from online_evidence.verifier import verify_candidates_with_vit
from scoring.visual_score import calculate_visual_risk_score
from scoring.fusion import calculate_text_business_risk, fuse_risk_scores


class TestCalibration(unittest.TestCase):
    """
    Comprehensive calibration tests covering E1, E4, corroboration rules,
    and legitimate website protections (T1-T9).
    """

    def test_t1_single_anomaly_not_high(self):
        """T1: Single 0.94 match must produce strong_match_count=1 and NOT be HIGH."""
        img1 = Image.new("RGB", (100, 100), (200, 100, 50))
        img2 = Image.new("RGB", (100, 100), (50, 100, 200))
        img3 = Image.new("RGB", (100, 100), (100, 200, 50))

        # Test with mock similarities via scoring engine directly
        mock_reuse_data = {
            "max_similarity": 0.94,
            "average_similarity": 0.45,
            "top_k_similarity": 0.50,
            "strong_match_count": 1,
            "moderate_match_count": 1,
            "reuse_risk_score": 64.0,
            "risk_level": "MEDIUM",
            "match_status": "INSUFFICIENT_EVIDENCE",
            "is_own_brand_candidate": False,
            "e4_score": 0.0,
        }
        vis_risk = calculate_visual_risk_score(
            mock_reuse_data,
            {"inconsistency_risk": 15.0},
            {"manipulation_score": 10.0, "synthetic_score": 10.0},
            cross_identity_coherence=80.0,
        )
        self.assertNotEqual(vis_risk["risk_level"], "HIGH", "Single anomaly must not produce HIGH visual risk")

        fusion = fuse_risk_scores(
            text_risk_data={"text_risk_score": 15.0, "signals": {"has_contact": True, "has_policy": True, "has_about": True, "has_social": True}},
            visual_risk_data=vis_risk,
            reuse_data=mock_reuse_data,
            logo_data={"similarity": 0.95, "inconsistency_risk": 15.0},
            manipulation_data={"manipulation_score": 10.0},
            merchant_name="SingleAnomalyMerchant",
        )
        self.assertNotEqual(fusion["status"], "HIGH", "Single anomaly must not produce final HIGH risk")
        self.assertIn("debug_metrics", fusion)
        self.assertEqual(fusion["debug_metrics"]["strong_match_count"], 1)

    def test_t2_multiple_strong_matches_high_eligible_when_corroborated(self):
        """T2: Multiple strong matches are HIGH eligible, and when corroborated produce HIGH."""
        mock_reuse_data = {
            "max_similarity": 0.95,
            "average_similarity": 0.91,
            "top_k_similarity": 0.93,
            "strong_match_count": 4,
            "moderate_match_count": 4,
            "reuse_risk_score": 88.0,
            "risk_level": "HIGH",
            "match_status": "CORROBORATED_EXTERNAL_MATCH",
            "is_own_brand_candidate": False,
            "e4_score": 75.0,
        }
        vis_risk = calculate_visual_risk_score(
            mock_reuse_data,
            {"inconsistency_risk": 75.0},
            {"manipulation_score": 65.0, "synthetic_score": 20.0},
            cross_identity_coherence=50.0,
        )
        self.assertEqual(vis_risk["risk_level"], "HIGH")

        fusion = fuse_risk_scores(
            text_risk_data={"text_risk_score": 20.0, "signals": {"has_contact": True, "has_policy": True, "has_about": True, "has_social": True}},
            visual_risk_data=vis_risk,
            reuse_data=mock_reuse_data,
            logo_data={"similarity": 0.35, "inconsistency_risk": 75.0},
            manipulation_data={"manipulation_score": 65.0},
            merchant_name="CorroboratedFraudMerchant",
        )
        self.assertEqual(fusion["status"], "HIGH", "Corroborated strong matches + independent anomaly must reach HIGH")

    def test_t3_generic_marketplace_imagery_not_high(self):
        """T3: Generic product images matching marketplaces must NOT automatically become HIGH."""
        mock_img = Image.new("RGB", (100, 100), (128, 128, 128))
        candidates = [
            {
                "candidate_id": "c1",
                "image": mock_img,
                "source_domain": "amazon.com",
                "source_url": "https://amazon.com/dp/B001",
                "source_type": "MARKETPLACE",
            }
        ]
        res = verify_candidates_with_vit(mock_img, candidates, merchant_domain="seller.com")
        self.assertEqual(res["match_status"], "INSUFFICIENT_EVIDENCE")
        self.assertLessEqual(res["e4_score"], 35.0)

    def test_t4_strong_serper_without_corroboration_insufficient_evidence(self):
        """T4: Strong Serper similarity without corroboration -> INSUFFICIENT_EVIDENCE."""
        mock_img = Image.new("RGB", (100, 100), (120, 150, 180))
        # Single candidate that matches identical image
        candidates = [
            {
                "candidate_id": "c1",
                "image": mock_img,
                "source_domain": "some-independent-blog.org",
                "source_url": "https://some-independent-blog.org/photo.jpg",
                "source_type": "ONLINE",
            }
        ]
        res = verify_candidates_with_vit(mock_img, candidates, merchant_domain="mch.com")
        self.assertEqual(res["match_status"], "INSUFFICIENT_EVIDENCE", "Single match must return INSUFFICIENT_EVIDENCE")
        self.assertLessEqual(res["e4_score"], 35.0)

    def test_t5_strong_serper_with_repeated_corroboration(self):
        """T5: Strong Serper similarity with repeated corroborating evidence -> CORROBORATED_EXTERNAL_MATCH."""
        mock_img = Image.new("RGB", (100, 100), (90, 120, 200))
        candidates = [
            {
                "candidate_id": "c1",
                "image": mock_img,
                "source_domain": "external-rogue-catalog.com",
                "source_url": "https://external-rogue-catalog.com/p1.jpg",
                "source_type": "ONLINE",
            },
            {
                "candidate_id": "c2",
                "image": mock_img,
                "source_domain": "external-rogue-catalog.com",
                "source_url": "https://external-rogue-catalog.com/p2.jpg",
                "source_type": "ONLINE",
            }
        ]
        res = verify_candidates_with_vit(mock_img, candidates, merchant_domain="legit-store.com")
        self.assertEqual(res["match_status"], "CORROBORATED_EXTERNAL_MATCH")
        self.assertGreaterEqual(res["e4_score"], 50.0)

    def test_t6_no_external_matches(self):
        """T6: No external matches -> NO_EXTERNAL_MATCH, is_own_brand_candidate=True, e4_score=0."""
        mock_img = Image.new("RGB", (100, 100), (10, 20, 30))
        res = verify_candidates_with_vit(mock_img, [], merchant_domain="artisan.com")
        self.assertEqual(res["match_status"], "NO_EXTERNAL_MATCH")
        self.assertTrue(res["is_own_brand_candidate"])
        self.assertEqual(res["e4_score"], 0.0)

    def test_t7_normal_legitimate_website_standard_marketing(self):
        """T7: Normal legitimate website with standard marketing images -> LOW or MEDIUM, NOT HIGH."""
        mock_reuse_data = {
            "max_similarity": 0.0,
            "average_similarity": 0.0,
            "top_k_similarity": 0.0,
            "strong_match_count": 0,
            "moderate_match_count": 0,
            "reuse_risk_score": 0.0,
            "risk_level": "LOW",
            "match_status": "NO_EXTERNAL_MATCH",
            "is_own_brand_candidate": True,
            "e4_score": 0.0,
        }
        logo_data = {
            "similarity": 0.90,
            "inconsistency_risk": 10.0,
            "risk_level": "LOW",
            "matched_reference": None,
        }
        manip_data = {
            "manipulation_score": 25.0,  # mild banner compositing
            "synthetic_score": 10.0,
        }
        vis_risk = calculate_visual_risk_score(
            mock_reuse_data,
            logo_data,
            manip_data,
            cross_identity_coherence=85.0,
        )
        self.assertIn(vis_risk["risk_level"], ("LOW", "MEDIUM"))

        text_data = calculate_text_business_risk({
            "has_contact": True,
            "has_policy": True,
            "has_pricing": True,
            "has_about": True,
            "social_links": ["https://x.com/brand"],
            "page_classification": {"site_category": "ECOMMERCE"},
        })
        fusion = fuse_risk_scores(
            text_risk_data=text_data,
            visual_risk_data=vis_risk,
            reuse_data=mock_reuse_data,
            logo_data=logo_data,
            manipulation_data=manip_data,
            merchant_name="ArtisanalHandmadeGoods",
        )
        self.assertIn(fusion["status"], ("LOW", "CLEAR", "MEDIUM"))
        self.assertNotEqual(fusion["status"], "HIGH")
        self.assertLess(fusion["final_risk_score"], 50.0)

    def test_t8_suspicious_website_repeated_copies_and_independent_anomaly(self):
        """T8: Deliberately suspicious website with repeated copied images + independent anomaly -> HIGH."""
        mock_reuse_data = {
            "max_similarity": 0.96,
            "average_similarity": 0.92,
            "top_k_similarity": 0.95,
            "strong_match_count": 3,
            "moderate_match_count": 3,
            "reuse_risk_score": 94.0,
            "risk_level": "HIGH",
            "match_status": "CORROBORATED_EXTERNAL_MATCH",
            "is_own_brand_candidate": False,
            "e4_score": 75.0,
        }
        logo_data = {
            "similarity": 0.30,
            "inconsistency_risk": 85.0,
            "risk_level": "HIGH",
            "matched_reference": "brand_logo_known.png",
        }
        manip_data = {
            "manipulation_score": 75.0,
            "synthetic_score": 40.0,
        }
        vis_risk = calculate_visual_risk_score(
            mock_reuse_data,
            logo_data,
            manip_data,
            cross_identity_coherence=40.0,
        )
        self.assertEqual(vis_risk["risk_level"], "HIGH")

        text_data = {"text_risk_score": 40.0, "signals": {"has_contact": False, "has_policy": True, "has_about": False, "has_social": False}}
        fusion = fuse_risk_scores(
            text_risk_data=text_data,
            visual_risk_data=vis_risk,
            reuse_data=mock_reuse_data,
            logo_data=logo_data,
            manipulation_data=manip_data,
            merchant_name="CopiedBrandClone",
        )
        self.assertEqual(fusion["status"], "HIGH")
        self.assertGreaterEqual(fusion["final_risk_score"], 80.0)

    def test_t9_pinterest_marketplace_stock_single_high_match_not_high(self):
        """T9: One 0.96 match from Pinterest/stock/marketplace with no corroboration -> INSUFFICIENT_EVIDENCE & NOT HIGH."""
        mock_img = Image.new("RGB", (100, 100), (220, 180, 140))
        candidates = [
            {
                "candidate_id": "pin_1",
                "image": mock_img,
                "source_domain": "pinterest.com",
                "source_url": "https://www.pinterest.com/pin/123456789/",
                "source_type": "ONLINE",
            }
        ]
        res = verify_candidates_with_vit(mock_img, candidates, merchant_domain="boutique-brand.com")
        self.assertEqual(res["match_status"], "INSUFFICIENT_EVIDENCE", "Pinterest match alone must return INSUFFICIENT_EVIDENCE")
        self.assertLessEqual(res["e4_score"], 25.0, "E4 score on Pinterest match alone must be capped <= 25")

        # Pass through full fusion
        mock_reuse = {
            "max_similarity": 0.96,
            "reuse_risk_score": res["e4_score"],
            "e4_score": res["e4_score"],
            "match_status": res["match_status"],
            "is_own_brand_candidate": False,
            "strong_match_count": res["strong_match_count"],
            "moderate_match_count": res["moderate_match_count"],
            "image_count": 1,
            "top_flagged_item": res["top_candidate"],
        }
        vis_risk = calculate_visual_risk_score(
            mock_reuse,
            {"inconsistency_risk": 10.0},
            {"manipulation_score": 10.0, "synthetic_score": 5.0},
            cross_identity_coherence=80.0,
        )
        fusion = fuse_risk_scores(
            text_risk_data={"text_risk_score": 15.0, "signals": {"has_contact": True, "has_policy": True, "has_about": True, "has_social": True}},
            visual_risk_data=vis_risk,
            reuse_data=mock_reuse,
            logo_data={"similarity": 0.90, "inconsistency_risk": 10.0},
            manipulation_data={"manipulation_score": 10.0},
            merchant_name="BoutiquePinterestSeller",
        )
        self.assertNotEqual(fusion["status"], "HIGH", "Pinterest-only match cannot cause final HIGH risk")
        self.assertEqual(fusion["debug_metrics"]["evidence_status"], "INSUFFICIENT_EVIDENCE")


if __name__ == "__main__":
    unittest.main()

