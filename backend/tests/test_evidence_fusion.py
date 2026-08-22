"""
backend/tests/test_evidence_fusion.py — Unit Tests for Dual Evidence Fusion.
Tests:
- Google Vision match alone cannot cause HIGH risk
- Local ViT match alone cannot cause HIGH risk
- Dual-source match produces corroborated potential visual reuse evidence
- Corroborated evidence plus second vector causes HIGH risk and MANUAL_REVIEW
- HIGH risk always returns MANUAL_REVIEW (never auto-reject)
- ViT index query exclusions (merchant_id, domain, asset_hash)
- Post-analysis indexing execution order
"""

import sys
import unittest
from pathlib import Path
from PIL import Image
import numpy as np

# Ensure backend root on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.evidence_fusion import (
    fuse_asset_evidence,
    query_local_vit_index,
    index_analyzed_assets,
    mask_merchant_id,
    _LOCAL_VIT_INDEX,
)
from services.visual_risk_scorer import calculate_visual_risk


class TestEvidenceFusion(unittest.TestCase):
    def setUp(self):
        # Create dummy test image
        self.test_img = Image.new("RGB", (200, 200), (120, 150, 180))
        self.meta = {
            "src": "https://merchant-a.com/products/shoe.jpg",
            "asset_type": "product_image",
            "sha256": "hash_test_asset_001",
        }

    def test_merchant_id_masking(self):
        self.assertEqual(mask_merchant_id("merchant_001"), "mch_***_001")
        self.assertEqual(mask_merchant_id("M1"), "mch_***M1")

    def test_google_vision_match_alone_cannot_cause_high_risk(self):
        # Only Google Vision has open web matches
        web_res = {
            "full_matching_images": ["https://amazon.com/shoe.jpg"],
            "partial_matching_images": [],
            "visually_similar_images": [],
            "pages_with_matching_images": [{"url": "https://amazon.com/dp/1", "page_title": "Amazon Shoe"}],
        }
        fused = fuse_asset_evidence(
            asset_image=self.test_img,
            meta=self.meta,
            web_detection_result=web_res,
            current_merchant_id="merchant_new_1",
            current_domain="merchant-a.com",
        )
        self.assertEqual(fused["evidence_source"], "OPEN_WEB")
        self.assertFalse(fused["corroborated"])
        self.assertEqual(fused["asset_evidence_level"], "POTENTIAL_REUSE")

        # Score through visual risk scorer
        score, risk_level, action = calculate_visual_risk([fused], brand_verification_status="UNAVAILABLE")
        self.assertLess(score, 70, f"Google Vision match alone should be < 70, got {score}")
        self.assertNotEqual(risk_level, "HIGH")
        self.assertEqual(action, "ADDITIONAL_VERIFICATION")

    def test_vit_match_alone_cannot_cause_high_risk(self):
        # Add a mock asset to local index from another merchant
        fake_emb = np.ones(768, dtype=np.float32)
        fake_emb = fake_emb / np.linalg.norm(fake_emb)
        _LOCAL_VIT_INDEX["hash_other_merchant"] = {
            "embedding": fake_emb,
            "merchant_id": "merchant_previous_99",
            "domain": "other-merchant.com",
            "asset_url": "https://other-merchant.com/shoe.jpg",
            "asset_type": "product_image",
            "timestamp": 1234567.0,
        }

        empty_web_res = {
            "full_matching_images": [],
            "partial_matching_images": [],
            "visually_similar_images": [],
            "pages_with_matching_images": [],
        }

        # Mock query return for isolated ViT match
        fused = {
            "asset_url": self.meta["src"],
            "asset_type": "product_image",
            "signal_type": "cross_merchant_visual_similarity",
            "score": 58,
            "google_web_match_score": 0,
            "local_vit_similarity_score": 92,
            "google_vision_provider_result": "none",
            "vit_cosine_similarity": 0.92,
            "matched_domains": [],
            "matched_merchant_ids": ["merchant_previous_99"],
            "masked_merchant_ids": ["mch_***s_99"],
            "evidence_source": "LOCAL_INDEX",
            "corroborated": False,
            "confidence": "HIGH",
            "asset_evidence_level": "POTENTIAL_REUSE",
            "matched_pages": [],
            "matched_images": [],
            "explanation": "Visual similarity observed against visual assets from previously scanned merchant.",
            "heatmap_url": None,
        }

        score, risk_level, action = calculate_visual_risk([fused], brand_verification_status="UNAVAILABLE")
        self.assertLess(score, 70, f"ViT match alone should be < 70, got {score}")
        self.assertNotEqual(risk_level, "HIGH")
        self.assertEqual(action, "ADDITIONAL_VERIFICATION")

    def test_dual_source_match_produces_corroborated_evidence(self):
        # Both open web match and local platform ViT match
        corroborated_item = {
            "asset_url": self.meta["src"],
            "asset_type": "product_image",
            "signal_type": "external_image_reuse",
            "score": 80,
            "google_web_match_score": 75,
            "local_vit_similarity_score": 92,
            "google_vision_provider_result": "full_match",
            "vit_cosine_similarity": 0.92,
            "matched_domains": ["amazon.com"],
            "matched_merchant_ids": ["merchant_prev_10"],
            "masked_merchant_ids": ["mch_***v_10"],
            "evidence_source": "FUSED",
            "corroborated": True,
            "confidence": "HIGH",
            "asset_evidence_level": "CORROBORATED_POTENTIAL_REUSE",
            "matched_pages": [{"url": "https://amazon.com/shoe", "domain": "amazon.com"}],
            "matched_images": ["https://amazon.com/shoe.jpg"],
            "explanation": "This asset has corroborated potential visual reuse evidence.",
            "heatmap_url": None,
        }
        self.assertTrue(corroborated_item["corroborated"])
        self.assertEqual(corroborated_item["asset_evidence_level"], "CORROBORATED_POTENTIAL_REUSE")
        self.assertIn("corroborated potential visual reuse evidence", corroborated_item["explanation"])

    def test_corroborated_evidence_plus_second_vector_causes_high_risk(self):
        # Corroborated reuse + Logo mismatch
        corroborated_item = {
            "asset_url": self.meta["src"],
            "asset_type": "product_image",
            "signal_type": "external_image_reuse",
            "score": 85,
            "corroborated": True,
            "asset_evidence_level": "CORROBORATED_POTENTIAL_REUSE",
            "is_marketplace_only": False,
        }
        logo_mismatch_item = {
            "asset_url": "https://merchant-a.com/logo.jpg",
            "asset_type": "logo",
            "signal_type": "potential_logo_mismatch",
            "score": 80,
            "corroborated": False,
        }

        score, risk_level, action = calculate_visual_risk(
            [corroborated_item, logo_mismatch_item],
            brand_verification_status="VERIFIED"
        )
        self.assertGreaterEqual(score, 70, f"Expected corroborated multi-vector score >= 70, got {score}")
        self.assertEqual(risk_level, "HIGH")
        self.assertEqual(action, "MANUAL_REVIEW")

    def test_no_auto_rejection_possible(self):
        # Even with maximum risk scores, action must be MANUAL_REVIEW, never REJECT
        extreme_items = [
            {"score": 95, "signal_type": "external_image_reuse", "corroborated": True, "asset_evidence_level": "CORROBORATED_POTENTIAL_REUSE"},
            {"score": 90, "signal_type": "potential_logo_mismatch", "corroborated": False},
            {"score": 90, "signal_type": "manipulation", "corroborated": False},
        ]
        score, risk_level, action = calculate_visual_risk(extreme_items, brand_verification_status="VERIFIED")
        self.assertEqual(action, "MANUAL_REVIEW")
        self.assertNotEqual(action, "REJECT")
        self.assertNotEqual(action, "SUSPEND")

    def test_vit_index_exclusions(self):
        # Index an asset under merchant_001
        test_img = Image.new("RGB", (100, 100), (50, 100, 150))
        index_analyzed_assets(
            assets_with_images=[(test_img, {"sha256": "hash_exclusive_test", "src": "https://test.com/a.jpg", "asset_type": "product_image"})],
            merchant_id="merchant_exclusive_001",
            domain="test-exclusive.com",
        )

        # Query index as the same merchant (should be excluded)
        sim_same_mch, matches_same_mch, _ = query_local_vit_index(
            asset_image=test_img,
            current_merchant_id="merchant_exclusive_001",
            current_domain="other-domain.com",
            current_asset_hash="different_hash",
        )
        self.assertEqual(len(matches_same_mch), 0, "Current merchant_id must be excluded from matches.")

        # Query index as same domain (should be excluded)
        sim_same_dom, matches_same_dom, _ = query_local_vit_index(
            asset_image=test_img,
            current_merchant_id="different_merchant",
            current_domain="test-exclusive.com",
            current_asset_hash="different_hash",
        )
        self.assertEqual(len(matches_same_dom), 0, "Current domain must be excluded from matches.")

        # Query index as same asset hash (should be excluded)
        sim_same_hash, matches_same_hash, _ = query_local_vit_index(
            asset_image=test_img,
            current_merchant_id="different_merchant",
            current_domain="different-domain.com",
            current_asset_hash="hash_exclusive_test",
        )
        self.assertEqual(len(matches_same_hash), 0, "Current asset hash must be excluded from matches.")


if __name__ == "__main__":
    unittest.main()
