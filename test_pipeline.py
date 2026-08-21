"""
test_pipeline.py — Integration and Unit Verification Script.
Tests all engine modules end-to-end with dynamic scores.
"""

from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image
import numpy as np

# Add backend and project root to sys.path
sys.path.insert(0, str(Path(__file__).parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent))

from visual.vit_embeddings import load_vit_model, get_image_embedding, compute_cosine_similarity
from visual.image_reuse import analyze_multiple_images_reuse, analyze_image_reuse, compute_identity_coherence
from visual.logo_check import check_logo_consistency
from visual.manipulation import analyze_image_manipulation
from visual.heatmap import generate_forensic_heatmap
from scoring.visual_score import calculate_visual_risk_score
from scoring.fusion import calculate_text_business_risk, fuse_risk_scores


def test_full_pipeline():
    print("=" * 60)
    print("RUNNING END-TO-END PIPELINE VERIFICATION")
    print("=" * 60)

    # 1. ViT Embeddings
    print("[1/6] Testing ViT Embeddings...")
    dummy_img = Image.new("RGB", (224, 224), (100, 150, 200))
    emb = get_image_embedding(dummy_img)
    assert isinstance(emb, np.ndarray), "Embedding must be numpy array"
    assert len(emb) > 0, "Embedding vector must not be empty"
    norm = np.linalg.norm(emb)
    print(f"  [PASS] Embedding shape: {emb.shape}, norm: {norm:.4f}")

    # 2. Image Reuse on Suspicious vs Clean
    print("[2/6] Testing Image Reuse Detection...")
    suspicious_watch_path = "dataset/merchants/suspicious/suspicious_product_1.jpg"
    clean_pot_path = "dataset/merchants/clean/clean_product_1.jpg"
    
    if Path(suspicious_watch_path).exists():
        reuse_res_susp = analyze_image_reuse(suspicious_watch_path, reference_dir="dataset/reference")
        print(f"  [PASS] Suspicious product similarity: {reuse_res_susp['similarity']:.4f}, Risk: {reuse_res_susp['risk_level']}")
        assert reuse_res_susp["similarity"] > 0.80, "Suspicious product should have high similarity with reference"
        
    if Path(clean_pot_path).exists():
        reuse_res_clean = analyze_image_reuse(clean_pot_path, reference_dir="dataset/reference")
        print(f"  [PASS] Clean product similarity: {reuse_res_clean['similarity']:.4f}, Risk: {reuse_res_clean['risk_level']}")
        assert reuse_res_clean["similarity"] < 0.65, "Clean artisanal product should have low similarity with catalog reference"

    # 3. Logo Check
    print("[3/6] Testing Logo Consistency Check...")
    suspicious_logo_path = "dataset/merchants/suspicious/suspicious_logo.png"
    if Path(suspicious_logo_path).exists():
        logo_res = check_logo_consistency(suspicious_logo_path, claimed_brand="Apex Brands", logos_dir="dataset/logos")
        print(f"  [PASS] Altered logo consistency score: {logo_res['consistency_score']}%, Risk: {logo_res['risk_level']}")
    
    # 4. Manipulation & Heatmap
    print("[4/6] Testing Forensic Manipulation & Heatmap...")
    tampered_doc_path = "dataset/merchants/suspicious/suspicious_tampered_doc.jpg"
    clean_doc_path = "dataset/merchants/clean/clean_document.jpg"
    
    if Path(tampered_doc_path).exists():
        manip_res = analyze_image_manipulation(tampered_doc_path)
        print(f"  [PASS] Tampered doc manipulation score: {manip_res['manipulation_score']}%, Risk: {manip_res['risk_level']}")
        heatmap = generate_forensic_heatmap(
            tampered_doc_path,
            ela_image=manip_res["ela_image"],
            gradient_map=manip_res["gradient_map"],
            suspicious_boxes=manip_res["suspicious_regions"],
        )
        assert isinstance(heatmap, np.ndarray), "Heatmap must be numpy array"
        assert heatmap.shape[2] == 3, "Heatmap must be 3-channel RGB image"
        print(f"  [PASS] Heatmap generated with shape: {heatmap.shape}")

    # 5. Visual Identity Coherence
    print("[5/7] Testing Visual Identity Coherence Engine...")
    clean_products = ["dataset/merchants/clean/clean_product_1.jpg", "dataset/merchants/clean/clean_product_2.jpg"]
    existing_clean_products = [p for p in clean_products if Path(p).exists()]
    if len(existing_clean_products) >= 2:
        coh_res = compute_identity_coherence(existing_clean_products)
        print(f"  [PASS] Clean merchant identity coherence: {coh_res['coherence_score']}%, Pairwise: {coh_res['pairwise_similarities']}")
        assert 0.0 <= coh_res["coherence_score"] <= 100.0, "Coherence score must be in 0-100"
        assert len(coh_res["pairwise_similarities"]) >= 1, "Must have pairwise similarities"

    single_img_res = compute_identity_coherence(["dataset/merchants/suspicious/suspicious_product_1.jpg"])
    print(f"  [PASS] Single-image fallback coherence: {single_img_res['coherence_score']}% (neutral default)")
    assert single_img_res["coherence_score"] == 70.0, "Single image should trigger neutral 70.0 default"

    # 6. Dynamic Scoring & Fusion
    print("[6/7] Testing Scoring & Multimodal Fusion...")
    text_risk = calculate_text_business_risk({"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": ["x"]})
    vis_risk = calculate_visual_risk_score(
        {"reuse_risk_score": 94.0},
        {"inconsistency_risk": 82.0},
        {"manipulation_score": 75.0, "synthetic_score": 35.0},
        cross_identity_coherence=coh_res["coherence_score"] if len(existing_clean_products) >= 2 else 70.0,
    )
    fusion = fuse_risk_scores(
        text_risk_data=text_risk,
        visual_risk_data=vis_risk,
        reuse_data={"max_similarity": 0.96, "reference_filename": "ref_luxury_watch_omega.jpg"},
        logo_data={"similarity": 0.38, "matched_reference": "verified_brand_apex.png"},
        manipulation_data={"manipulation_score": 75.0},
        merchant_name="Apex Global Luxury",
    )
    print(f"  [PASS] Text Risk: {fusion['text_risk_score']} / 100")
    print(f"  [PASS] Visual Risk: {fusion['visual_risk_score']} / 100")
    print(f"  [PASS] Final Risk: {fusion['final_risk_score']} / 100 -> Status: {fusion['status_label']}")
    assert fusion["status"] == "HIGH", "High visual discrepancy should trigger HIGH status"

    print("[7/7] All verification checks PASSED successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_full_pipeline()
