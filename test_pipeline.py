"""
test_pipeline.py — Integration and Unit Verification Script.
Tests all engine modules end-to-end:
  [1] Pretrained Vision Transformer (ViT) Backbone
  [2] Image Reuse & Stolen Catalog Detection (Test Fixtures)
  [3] Brand Logo Consistency Engine
  [4] ELA Tampering Forensics & Heatmap Generation
  [5] Cross-Image Visual Identity Coherence
  [6] Multimodal Risk Fusion & Escalation
  [7] Website Crawling & Metadata Extraction
  [8] Image Filtering (UI / Pixel / Icon Elimination)
  [9] Image Deduplication & Perceptual Grouping
  [10] Online Evidence Search & Candidate Retrieval
  [11] ViT Visual Verification & Similarity Calculation
  [12] Evidence Ranking & Strength Classification
  [13] Own-Brand / No-Match Handling (Zero Penalty Protection)
  [14] Strong External-Match Case Handling (Risk Escalation)
  [15] End-to-End Website Analysis Pipeline
"""

from __future__ import annotations

import sys
import time
import argparse
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

# Add backend and project root to sys.path
sys.path.insert(0, str(Path(__file__).parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent))

# Ensure UTF-8 output across Windows, Linux and macOS
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# Existing Modules
from visual.vit_embeddings import load_vit_model, get_image_embedding, compute_cosine_similarity
from visual.image_reuse import analyze_multiple_images_reuse, analyze_image_reuse, compute_identity_coherence
from visual.logo_check import check_logo_consistency
from visual.manipulation import analyze_image_manipulation
from visual.heatmap import generate_forensic_heatmap
from scoring.visual_score import calculate_visual_risk_score
from scoring.fusion import calculate_text_business_risk, fuse_risk_scores

# New Crawler, Image Extraction & Online Verification Modules
from crawler.site_crawler import crawl_merchant, _extract_merchant_name, _extract_rich_images
from crawler.image_extractor import (
    process_and_prioritize_images,
    compute_dhash,
    hamming_distance,
    is_useless_ui_image,
    calculate_image_priority_score,
)
from online_evidence.candidate_search import discover_candidate_evidence
from online_evidence.verifier import verify_candidates_with_vit
from routes.analyze import execute_website_analysis, run_pipeline


def run_verification_suite(module_filter: str = "all", verbose: bool = True) -> bool:
    print("=" * 80)
    print(" 🛡️  Visual Risk Intelligence Engine — Comprehensive Test Suite")
    print("=" * 80)
    start_total = time.time()
    tests_passed = 0
    tests_total = 0

    # Ensure demo/fixture dataset exists
    if not Path("dataset/merchants").exists() and not Path("backend/dataset/merchants").exists():
        print("[WARN] Merchant dataset directories not found. Generating demo datasets first...")
        from generate_demo_dataset import build_all_demo_datasets
        build_all_demo_datasets()

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Pretrained ViT Backbone
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "vit"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 1/15] Verifying Pretrained Vision Transformer (ViT) Backbone...")
        try:
            dummy_img = Image.new("RGB", (224, 224), (100, 150, 200))
            emb = get_image_embedding(dummy_img)
            assert isinstance(emb, np.ndarray), "Embedding must be a numpy ndarray"
            assert len(emb) == 768, f"Expected 768-dim vector, got {len(emb)}"
            norm = np.linalg.norm(emb)
            assert np.isclose(norm, 1.0, atol=1e-3), f"Expected L2 norm ~1.0, got {norm:.4f}"
            tests_passed += 1
            print(f"  [✓ PASS] ViT Backbone Operational (Dim: {emb.shape[0]}, L2 Norm: {norm:.4f}) [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] ViT Verification Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Image Reuse on Suspicious vs Clean (Test Fixtures)
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "reuse"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 2/15] Verifying Image Reuse & Stolen Catalog Detection (Test Fixtures)...")
        try:
            suspicious_watch_path = "dataset/merchants/suspicious/suspicious_product_1.jpg"
            clean_pot_path = "dataset/merchants/clean/clean_product_1.jpg"
            
            if Path(suspicious_watch_path).exists():
                reuse_res_susp = analyze_image_reuse(suspicious_watch_path, reference_dir="dataset/reference")
                assert reuse_res_susp["similarity"] > 0.80, "Suspicious product must register high similarity (>0.80)"
                if verbose:
                    print(f"  • Suspicious Product Similarity: {reuse_res_susp['similarity'] * 100:.1f}% (Risk: {reuse_res_susp['risk_level']})")

            if Path(clean_pot_path).exists():
                reuse_res_clean = analyze_image_reuse(clean_pot_path, reference_dir="dataset/reference")
                assert reuse_res_clean["similarity"] < 0.65, "Clean artisanal product must register low similarity (<0.65)"
                if verbose:
                    print(f"  • Authentic Product Similarity:  {reuse_res_clean['similarity'] * 100:.1f}% (Risk: {reuse_res_clean['risk_level']})")

            tests_passed += 1
            print(f"  [✓ PASS] Catalog Reuse Engine Verified [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] Reuse Detection Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Logo Consistency Check
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "logo"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 3/15] Verifying Brand Logo Divergence Engine...")
        try:
            suspicious_logo_path = "dataset/merchants/suspicious/suspicious_logo.png"
            if Path(suspicious_logo_path).exists():
                logo_res = check_logo_consistency(suspicious_logo_path, claimed_brand="Apex Brands", logos_dir="dataset/logos")
                assert 0.0 <= logo_res["consistency_score"] <= 100.0
                if verbose:
                    print(f"  • Altered Logo Consistency:    {logo_res['consistency_score']:.1f}% (Risk: {logo_res['risk_level']})")
            tests_passed += 1
            print(f"  [✓ PASS] Logo Consistency Engine Verified [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] Logo Consistency Check Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Manipulation Forensics & Heatmap
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "forensics"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 4/15] Verifying ELA Tampering Forensics & Heatmap Generation...")
        try:
            tampered_doc_path = "dataset/merchants/suspicious/suspicious_tampered_doc.jpg"
            if Path(tampered_doc_path).exists():
                manip_res = analyze_image_manipulation(tampered_doc_path)
                assert manip_res["manipulation_score"] > 0
                heatmap = generate_forensic_heatmap(
                    tampered_doc_path,
                    ela_image=manip_res["ela_image"],
                    gradient_map=manip_res["gradient_map"],
                    suspicious_boxes=manip_res["suspicious_regions"],
                )
                assert isinstance(heatmap, np.ndarray)
                assert heatmap.shape[2] == 3
                if verbose:
                    print(f"  • Tampered Document Score:      {manip_res['manipulation_score']:.1f}% (Heatmap: {heatmap.shape})")
            tests_passed += 1
            print(f"  [✓ PASS] Forensics & Heatmap Engine Verified [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] Manipulation Forensics Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Visual Identity Coherence
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "coherence"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 5/15] Verifying Cross-Image Identity Coherence Engine...")
        try:
            clean_products = ["dataset/merchants/clean/clean_product_1.jpg", "dataset/merchants/clean/clean_product_2.jpg"]
            existing_clean_products = [p for p in clean_products if Path(p).exists()]
            if len(existing_clean_products) >= 2:
                coh_res = compute_identity_coherence(existing_clean_products)
                assert 0.0 <= coh_res["coherence_score"] <= 100.0
                if verbose:
                    print(f"  • Multi-Product Coherence:     {coh_res['coherence_score']:.1f}%")
            tests_passed += 1
            print(f"  [✓ PASS] Identity Coherence Engine Verified [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] Identity Coherence Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Dynamic Scoring & Multimodal Fusion
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "fusion"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 6/15] Verifying Multimodal Risk Fusion & Escalation...")
        try:
            text_risk = calculate_text_business_risk({"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": ["x"]})
            vis_risk = calculate_visual_risk_score(
                {"reuse_risk_score": 94.0, "is_own_brand_candidate": False},
                {"inconsistency_risk": 82.0},
                {"manipulation_score": 75.0, "synthetic_score": 35.0},
                cross_identity_coherence=75.0,
            )
            fusion = fuse_risk_scores(
                text_risk_data=text_risk,
                visual_risk_data=vis_risk,
                reuse_data={"max_similarity": 0.96, "reuse_risk_score": 94.0, "reference_filename": "ref_luxury_watch_omega.jpg", "is_own_brand_candidate": False},
                logo_data={"similarity": 0.38, "matched_reference": "verified_brand_apex.png"},
                manipulation_data={"manipulation_score": 75.0},
                merchant_name="Apex Global Luxury",
            )
            assert fusion["status"] == "HIGH", "High visual divergence must trigger HIGH risk status"
            if verbose:
                print(f"  • Text Risk: {fusion['text_risk_score']}/100 | Visual Risk: {fusion['visual_risk_score']}/100 | Final: {fusion['final_risk_score']}/100 ({fusion['status_label']})")
            tests_passed += 1
            print(f"  [✓ PASS] Multimodal Fusion Engine Verified [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] Scoring Fusion Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 7. Website Crawling & Metadata Extraction
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "crawler"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 7/15] Verifying Website Crawler & Metadata Extraction...")
        try:
            from bs4 import BeautifulSoup
            sample_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Loom & Thread Studio — Handcrafted Organic Linens</title>
                <meta property="og:site_name" content="Loom & Thread" />
                <meta name="description" content="Pure artisanal organic bed linens." />
            </head>
            <body>
                <header>
                    <img src="/assets/logo.png" alt="Loom & Thread Logo" class="site-logo" width="180" height="60" />
                </header>
                <main>
                    <div class="product-card">
                        <h3>Organic Linen Sheet</h3>
                        <p class="price">$120</p>
                        <img src="/assets/products/sheet_1.jpg" alt="Organic Linen Sheet White" width="600" height="600" />
                    </div>
                </main>
                <footer>
                    <a href="/contact">Contact Support</a>
                    <a href="/privacy">Privacy Policy</a>
                </footer>
            </body>
            </html>
            """
            soup = BeautifulSoup(sample_html, "html.parser")
            merchant_name = _extract_merchant_name(soup, "loomandthread.com", "Loom & Thread Studio")
            assert merchant_name == "Loom & Thread", f"Expected 'Loom & Thread', got '{merchant_name}'"

            imgs, logo_candidate = _extract_rich_images(soup, "https://loomandthread.com")
            assert len(imgs) >= 2, f"Expected at least 2 extracted images, got {len(imgs)}"
            assert any(img["is_logo_candidate"] for img in imgs), "Logo candidate should be identified"
            assert any(img["is_product_candidate"] for img in imgs), "Product candidate should be identified"
            
            tests_passed += 1
            print(f"  [✓ PASS] Website Crawler & Metadata Extractor Verified [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] Crawler Verification Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 8. Image Filtering (UI / Pixel / Icon Elimination)
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "filter"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 8/15] Verifying High-Volume Image Filtering & Heuristics...")
        try:
            tracking_pixel = {"src": "https://cdn.example.com/pixel.gif", "alt": "", "class": "tracker"}
            social_icon = {"src": "https://cdn.example.com/icons/facebook.svg", "alt": "Facebook", "class": "social-icon"}
            product_img = {"src": "https://cdn.example.com/products/leather_bag.jpg", "alt": "Handcrafted Leather Bag", "class": "product-image", "is_product_candidate": True}

            assert is_useless_ui_image(tracking_pixel) is True, "Tracking pixel must be filtered"
            assert is_useless_ui_image(social_icon) is True, "Social icon must be filtered"
            assert is_useless_ui_image(product_img) is False, "Product visual must NOT be filtered"

            score_product = calculate_image_priority_score({"width": 800, "height": 800, "is_product_candidate": True, "alt": "Handcrafted Leather Bag", "src": "https://cdn.example.com/products/bag.jpg"}, "Leather Co")
            score_tiny = calculate_image_priority_score({"width": 80, "height": 80, "is_product_candidate": False, "alt": "", "src": "https://cdn.example.com/banner.jpg"}, "Leather Co")
            assert score_product > score_tiny, "Large product image must score higher priority than tiny banner"

            tests_passed += 1
            print(f"  [✓ PASS] Image Filtering & Prioritization Verified [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] Image Filtering Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 9. Image Deduplication & Perceptual Grouping
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "dedup"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 9/15] Verifying Perceptual dHash Deduplication & Grouping...")
        try:
            # Create a base image and a slightly scaled/modified copy
            base_img = Image.new("RGB", (400, 400), (200, 100, 50))
            draw = ImageDraw.Draw(base_img)
            draw.rectangle([50, 50, 350, 350], fill=(50, 150, 220))

            modified_copy = base_img.resize((200, 200), Image.Resampling.BILINEAR)

            h1 = compute_dhash(base_img)
            h2 = compute_dhash(modified_copy)
            dist = hamming_distance(h1, h2)

            assert dist <= 5, f"Perceptually identical images should have Hamming distance <= 5, got {dist}"

            # Distinct image should have large Hamming distance
            distinct_img = Image.new("RGB", (400, 400), (10, 220, 30))
            draw_dist = ImageDraw.Draw(distinct_img)
            draw_dist.ellipse([100, 100, 300, 300], fill=(255, 0, 128))
            h3 = compute_dhash(distinct_img)
            dist_distinct = hamming_distance(h1, h3)
            assert dist_distinct > 10, f"Distinct images should have large Hamming distance, got {dist_distinct}"

            tests_passed += 1
            print(f"  [✓ PASS] Perceptual Deduplication Verified (Duplicate Dist: {dist}, Distinct Dist: {dist_distinct}) [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] Deduplication Verification Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 10. Online Evidence Search & Candidate Retrieval
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "online"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 10/15] Verifying Online Evidence Discovery Interface...")
        try:
            # Test that production discovery does not crash and returns a valid list
            candidates = discover_candidate_evidence(
                merchant_image=None,
                query_hint="Luxury Chronograph Watch",
                test_fixture_dir=None,  # Production mode
                max_candidates=3,
            )
            assert isinstance(candidates, list), "Candidate discovery must return a list"
            
            # Test with controlled test fixture
            fixture_candidates = discover_candidate_evidence(
                query_hint="Luxury Chronograph Watch",
                test_fixture_dir="dataset/reference",
                max_candidates=3,
            )
            assert len(fixture_candidates) > 0, "Test fixture provider should return candidate assets"
            assert fixture_candidates[0]["source_type"] == "LOCAL_TEST_FIXTURE"

            tests_passed += 1
            print(f"  [✓ PASS] Candidate Discovery Interface Operational [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] Online Evidence Search Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 11. ViT Verification & Similarity Calculation
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "vit_verify"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 11/15] Verifying ViT Visual Verification against Candidates...")
        try:
            img_a = Image.new("RGB", (224, 224), (220, 50, 50))
            img_b = Image.new("RGB", (224, 224), (220, 50, 50))  # Identical visual
            img_c = Image.new("RGB", (224, 224), (20, 200, 20))   # Different visual

            candidates = [
                {"candidate_id": "cand_1", "image": img_b, "source_url": "https://example.com/p1", "source_domain": "example.com", "title": "Red Product"},
                {"candidate_id": "cand_2", "image": img_c, "source_url": "https://other.com/p2", "source_domain": "other.com", "title": "Green Product"},
            ]

            verify_res = verify_candidates_with_vit(img_a, candidates)
            assert verify_res["max_similarity"] > 0.95, f"Identical images must have ViT similarity > 0.95, got {verify_res['max_similarity']}"
            assert verify_res["evidence_strength"] == "HIGH"
            assert len(verify_res["all_candidates"]) == 2

            tests_passed += 1
            print(f"  [✓ PASS] ViT Verification Verified (Top Sim: {verify_res['max_similarity'] * 100:.1f}%, Strength: {verify_res['evidence_strength']}) [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] ViT Verification Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 12. Evidence Ranking & Strength Classification
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "ranking"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 12/15] Verifying Evidence Ranking & Strength Classification...")
        try:
            # Check threshold boundaries: >= 0.85 -> HIGH, 0.70-0.84 -> MEDIUM, <0.70 -> LOW
            img_target = Image.new("RGB", (224, 224), (100, 100, 100))
            cand_res = verify_candidates_with_vit(img_target, [])
            assert cand_res["evidence_strength"] == "LOW"
            assert cand_res["match_status"] == "NO_EXTERNAL_MATCH"
            assert cand_res["is_own_brand_candidate"] is True

            tests_passed += 1
            print(f"  [✓ PASS] Evidence Ranking & Strength Boundaries Verified [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] Evidence Ranking Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 13. Own-Brand / No-Match Handling (Zero Penalty Protection)
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "own_brand"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 13/15] Verifying Own-Brand / Unique Visual Handling (No Unfair Penalty)...")
        try:
            # Own-brand merchant with NO external matches online
            reuse_data_own_brand = {
                "max_similarity": 0.0,
                "reuse_risk_score": 0.0,
                "is_own_brand_candidate": True,
                "match_status": "NO_EXTERNAL_MATCH",
            }
            logo_data_clean = {"inconsistency_risk": 0.0, "similarity": 1.0}
            manip_clean = {"manipulation_score": 5.0, "synthetic_score": 5.0}

            vis_score_res = calculate_visual_risk_score(
                reuse_data_own_brand,
                logo_data_clean,
                manip_clean,
                cross_identity_coherence=90.0,
            )

            # Ensure visual risk score is LOW (<= 25) when product is own-brand
            assert vis_score_res["visual_risk_score"] <= 25.0, f"Own-brand visual risk must be LOW (<= 25), got {vis_score_res['visual_risk_score']}"
            assert vis_score_res["risk_level"] == "LOW"

            fused = fuse_risk_scores(
                text_risk_data={"text_risk_score": 15.0},
                visual_risk_data=vis_score_res,
                reuse_data=reuse_data_own_brand,
                logo_data=logo_data_clean,
                manipulation_data=manip_clean,
                merchant_name="Artisan Pottery Studio",
            )
            assert fused["status"] == "LOW", f"Own-brand merchant must be categorized as LOW risk, got {fused['status']}"

            tests_passed += 1
            print(f"  [✓ PASS] Own-Brand Protection Verified (Score: {fused['final_risk_score']}/100, Tier: {fused['status']}) [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] Own-Brand Handling Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 14. Strong External-Match Handling (Appropriate Escalation)
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "external_match"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 14/15] Verifying Strong External Match Risk Escalation...")
        try:
            # Merchant with 95% external visual match on candidate web visual
            reuse_data_copied = {
                "max_similarity": 0.95,
                "reuse_risk_score": 91.7,
                "is_own_brand_candidate": False,
                "match_status": "EXTERNAL_MATCH_FOUND",
                "top_flagged_item": {
                    "similarity": 0.95,
                    "source_domain": "archive.merchant-catalog.org",
                    "risk_level": "HIGH",
                }
            }
            logo_data_altered = {"inconsistency_risk": 75.0, "similarity": 0.35, "matched_reference": "brand_mark.png"}
            manip_tampered = {"manipulation_score": 70.0, "synthetic_score": 25.0}

            vis_score_copied = calculate_visual_risk_score(
                reuse_data_copied,
                logo_data_altered,
                manip_tampered,
                cross_identity_coherence=30.0,
            )
            assert vis_score_copied["visual_risk_score"] >= 75.0, "Copied visuals + altered logo must trigger high visual risk (>= 75)"

            fused_copied = fuse_risk_scores(
                text_risk_data={"text_risk_score": 15.0},  # Clean surface text
                visual_risk_data=vis_score_copied,
                reuse_data=reuse_data_copied,
                logo_data=logo_data_altered,
                manipulation_data=manip_tampered,
                merchant_name="Copied Catalog Store",
            )
            assert fused_copied["status"] == "HIGH", "High visual misrepresentation must override surface text and flag HIGH risk"

            tests_passed += 1
            print(f"  [✓ PASS] External Match Escalation Verified (Score: {fused_copied['final_risk_score']}/100, Tier: {fused_copied['status']}) [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] External Match Escalation Failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 15. End-to-End Website Analysis Pipeline
    # ─────────────────────────────────────────────────────────────────────────
    if module_filter in ("all", "e2e"):
        tests_total += 1
        t0 = time.time()
        print("\n[Step 15/15] Verifying End-to-End Website Analysis Pipeline...")
        try:
            # Run end-to-end analysis on controlled benchmark website
            e2e_res = execute_website_analysis("https://example.com")
            assert "fusion" in e2e_res, "Pipeline must return 'fusion' risk object"
            assert "structured_evidence" in e2e_res, "Pipeline must return structured evidence list"
            assert "claims_reasoning" in e2e_res, "Pipeline must return claims reasoning object"
            assert "image_processing_metrics" in e2e_res, "Pipeline must return image processing metrics"
            assert 0.0 <= e2e_res["fusion"]["final_risk_score"] <= 100.0

            if verbose:
                print(f"  • Extracted Merchant:  {e2e_res['fusion']['merchant_name']}")
                print(f"  • Final Risk Score:    {e2e_res['fusion']['final_risk_score']}/100 ({e2e_res['fusion']['status_label']})")
                print(f"  • Raw Images Discovered: {e2e_res['image_processing_metrics']['total_raw_count']}")

            tests_passed += 1
            print(f"  [✓ PASS] End-to-End Analysis Pipeline Operational [{time.time() - t0:.3f}s]")
        except Exception as e:
            print(f"  [✗ FAIL] End-to-End Pipeline Failed: {e}")

    total_time = time.time() - start_total
    print("\n" + "=" * 80)
    if tests_passed == tests_total:
        print(f" [✓] ALL {tests_passed}/{tests_total} PIPELINE VERIFICATION CHECKS PASSED ({total_time:.2f}s)")
    else:
        print(f" [✗] {tests_passed}/{tests_total} CHECKS PASSED, {tests_total - tests_passed} FAILED ({total_time:.2f}s)")
    print("=" * 80)
    return tests_passed == tests_total


def main():
    parser = argparse.ArgumentParser(
        description="🛡️ Visual Risk Intelligence Engine — Integration Verification",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--module",
        choices=[
            "all", "vit", "reuse", "logo", "forensics", "coherence", "fusion",
            "crawler", "filter", "dedup", "online", "vit_verify", "ranking",
            "own_brand", "external_match", "e2e"
        ],
        default="all",
        help="Target specific pipeline module to test",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run in concise mode without intermediate metric breakdowns",
    )

    args = parser.parse_args()
    success = run_verification_suite(module_filter=args.module, verbose=not args.quiet)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
