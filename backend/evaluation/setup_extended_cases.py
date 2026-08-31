import json
import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

BACKEND_DIR = Path(__file__).resolve().parent.parent
EVAL_ROOT = BACKEND_DIR / "dataset" / "eval_set"
REF_DIR = BACKEND_DIR / "dataset" / "reference"
MERCHANTS_DIR = BACKEND_DIR / "dataset" / "merchants"
LOGOS_DIR = BACKEND_DIR / "dataset" / "logos"

def setup_extended_cases():
    # 1. Enrich existing 18 cases with case_type, ground_truth_risk_tier, expected_evidence_summary
    case_type_map = {
        # Clean (6)
        "clean_01_artisanal_terracotta": ("legitimate_merchant", "LOW", "Artisanal handcrafted ceramics; proprietary visuals with zero external matches and complete compliance disclosures."),
        "clean_02_flora_linen": ("no_external_evidence", "LOW", "Proprietary organic linen studio catalog; zero external visual matches discovered."),
        "clean_03_artisan_leathercraft": ("ambiguous_insufficient_evidence", "LOW", "Handmade custom leather goods; single uncorroborated reference match with no secondary risk signals; classified as LOW."),
        "clean_04_aura_glassworks": ("legitimate_merchant", "LOW", "Handblown studio glassware; unique proprietary imagery with verified business profile."),
        "clean_05_timber_craft_studio": ("legitimate_merchant", "LOW", "Artisan woodworking studio; proprietary catalog photos and standard legal disclosures."),
        "clean_06_solstice_bespoke_gems": ("no_external_evidence", "LOW", "Bespoke handcrafted gemstone jewelry; unique visual assets and full business contact details."),
        
        # Borderline (6)
        "bord_01_urban_distributor": ("supplier_catalog_reuse", "MEDIUM", "Regional footwear reseller; supplier catalog overlap with minor logo variance and partial text disclosures."),
        "bord_02_audio_direct_outlet": ("supplier_catalog_reuse", "MEDIUM", "Consumer audio outlet; authorized supplier imagery with missing pricing disclosure."),
        "bord_03_metro_streetwear": ("supplier_catalog_reuse", "MEDIUM", "Urban streetwear distributor; multi-brand supplier catalog with missing contact channel."),
        "bord_04_commuter_utility_bags": ("supplier_catalog_reuse", "MEDIUM", "Backpack & utility bag reseller; supplier catalog reuse with missing return policy disclosure."),
        "bord_05_sports_audio_lab": ("supplier_catalog_reuse", "MEDIUM", "Athletic audio partner; multi-brand distributor visuals with missing about disclosure."),
        "bord_06_lifestyle_collective": ("supplier_catalog_reuse", "MEDIUM", "Lifestyle accessories distributor; supplier catalog imagery with missing pricing and policy disclosures."),

        # Suspicious (6)
        "susp_01_stolen_chronographs": ("suspicious_external_match", "HIGH", "Claims official Apex Brands luxury watch flagship; plagiarized luxury chronograph imagery with trademark logo divergence."),
        "susp_02_cloned_designer_leather": ("fake_distorted_logo", "HIGH", "Claims official Luxe Atelier flagship; stolen designer handbag photos paired with distorted counterfeit logo."),
        "susp_03_reused_airmax_store": ("suspicious_external_match", "HIGH", "Claims exclusive Apex athletic footwear flagship; stolen reference sneaker imagery with trademark divergence."),
        "susp_04_pro_audio_clones": ("suspicious_external_match", "HIGH", "Claims authorized Apex wireless audio flagship; copied electronics imagery with trademark divergence."),
        "susp_05_luxury_gold_horology": ("suspicious_external_match", "HIGH", "Claims official Apex horology flagship; stolen luxury timepiece visuals with brand claim mismatch."),
        "susp_06_counterfeit_tote_bazaar": ("fake_distorted_logo", "HIGH", "Claims official Luxe Atelier store; copied designer tote imagery with severely altered trademark logo."),
    }

    for case_id, (ctype, gt_tier, exp_summary) in case_type_map.items():
        found = list(EVAL_ROOT.glob(f"*/*{case_id}*"))
        if found and found[0].is_dir():
            meta_p = found[0] / "meta.json"
            if meta_p.exists():
                meta = json.loads(meta_p.read_text(encoding="utf-8"))
                meta["case_type"] = ctype
                meta["ground_truth_risk_tier"] = gt_tier
                meta["expected_evidence_summary"] = exp_summary
                meta_p.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # 2. Add Missing Case Types
    # Case A: Stock Image Reuse (bord_07_stock_decor_emporium) -> Borderline (MEDIUM)
    stock_dir = EVAL_ROOT / "borderline" / "stock_01_modern_home_decor"
    stock_dir.mkdir(parents=True, exist_ok=True)
    # Create product image
    p1 = Image.open(MERCHANTS_DIR / "borderline" / "borderline_product_1.jpg").convert("RGB")
    p1.save(stock_dir / "product_1.jpg", "JPEG", quality=95)
    shutil.copy(MERCHANTS_DIR / "clean" / "clean_logo.png", stock_dir / "logo.png")
    shutil.copy(MERCHANTS_DIR / "clean" / "clean_document.jpg", stock_dir / "document.jpg")
    (stock_dir / "meta.json").write_text(json.dumps({
        "name": "Nordic Living Home Decor",
        "category": "Home Decor & Furnishings",
        "claimed_brand": "Nordic Living",
        "ground_truth": "MEDIUM",
        "case_type": "stock_image_reuse",
        "ground_truth_risk_tier": "MEDIUM",
        "expected_evidence_summary": "Stock catalog image reuse detected without brand trademark infringement or document tampering; classified for standard merchant review.",
        "claims": {
            "inventory_claim": "Curated catalog of Nordic home decor.",
            "brand_claim": "Nordic Living home goods.",
            "compliance_claim": "Registered business entity certificate."
        },
        "crawler_data": {
            "has_contact": True,
            "has_policy": True,
            "has_pricing": True,
            "has_about": False,
            "social_links": ["https://instagram.com/nordicliving"]
        }
    }, indent=2), encoding="utf-8")

    # Case B: Cross-Merchant Catalog Reuse (bord_08_cross_merchant_apparel) -> Borderline (MEDIUM)
    cross_dir = EVAL_ROOT / "borderline" / "cross_01_duplicated_apparel_store"
    cross_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(EVAL_ROOT / "clean" / "clean_02_flora_linen" / "product_1.jpg", cross_dir / "product_1.jpg")
    shutil.copy(MERCHANTS_DIR / "borderline" / "borderline_logo.png", cross_dir / "logo.png")
    shutil.copy(MERCHANTS_DIR / "borderline" / "borderline_document.jpg", cross_dir / "document.jpg")
    (cross_dir / "meta.json").write_text(json.dumps({
        "name": "Urban Fabric Express",
        "category": "Apparel & Textiles",
        "claimed_brand": "Urban Fabric",
        "ground_truth": "MEDIUM",
        "case_type": "cross_merchant_reuse",
        "ground_truth_risk_tier": "MEDIUM",
        "expected_evidence_summary": "Cross-merchant product imagery duplication matches previously scanned platform merchant; requires distributor verification.",
        "claims": {
            "inventory_claim": "Regional apparel distributor catalog.",
            "brand_claim": "Urban Fabric distribution partner.",
            "compliance_claim": "Standard digital registration copy."
        },
        "crawler_data": {
            "has_contact": True,
            "has_policy": True,
            "has_pricing": True,
            "has_about": False,
            "social_links": []
        }
    }, indent=2), encoding="utf-8")

    # Case C: Manipulated Document (susp_07_tampered_incorporation_cert) -> Suspicious (HIGH)
    manip_doc_dir = EVAL_ROOT / "suspicious" / "susp_07_tampered_incorporation_cert"
    manip_doc_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(MERCHANTS_DIR / "clean" / "clean_product_1.jpg", manip_doc_dir / "product_1.jpg")
    shutil.copy(MERCHANTS_DIR / "clean" / "clean_logo.png", manip_doc_dir / "logo.png")
    
    # Create high-ELA tampered document
    doc_base = Image.open(MERCHANTS_DIR / "clean" / "clean_document.jpg").convert("RGB")
    doc_draw = ImageDraw.Draw(doc_base)
    # Splice a forged text block with distinct recompression
    w, h = doc_base.size
    doc_draw.rectangle([w * 0.2, h * 0.45, w * 0.8, h * 0.58], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
    doc_draw.text((w * 0.22, h * 0.47), "FORGED REGISTRATION AMENDMENT: REG-998822-X", fill=(10, 10, 10))
    doc_draw.text((w * 0.22, h * 0.52), "AUTHORIZED GLOBAL OFFSHORE ENTITY DISCLOSURE", fill=(180, 20, 20))
    doc_base.save(manip_doc_dir / "document.jpg", "JPEG", quality=80)
    
    (manip_doc_dir / "meta.json").write_text(json.dumps({
        "name": "Vanguard Global Imports",
        "category": "Commercial Import & Export",
        "claimed_brand": "Vanguard Global",
        "ground_truth": "HIGH",
        "case_type": "manipulated_document",
        "ground_truth_risk_tier": "HIGH",
        "expected_evidence_summary": "Statutory registration certificate contains severe localized manipulation and ELA gradient disparities.",
        "claims": {
            "inventory_claim": "Direct importer inventory.",
            "brand_claim": "Vanguard Global commercial trade.",
            "compliance_claim": "Statutory Incorporation Certificate."
        },
        "crawler_data": {
            "has_contact": True,
            "has_policy": False,
            "has_pricing": True,
            "has_about": False,
            "social_links": []
        }
    }, indent=2), encoding="utf-8")

    # Case D: Manipulated Product Image (susp_08_spliced_luxury_watch) -> Suspicious (HIGH)
    spliced_prod_dir = EVAL_ROOT / "suspicious" / "susp_08_spliced_luxury_watch"
    spliced_prod_dir.mkdir(parents=True, exist_ok=True)
    
    # Create spliced product image
    watch_img = Image.open(REF_DIR / "ref_luxury_watch_omega.jpg").convert("RGB")
    w_draw = ImageDraw.Draw(watch_img)
    pw, ph = watch_img.size
    # Splice an artificial high-contrast counterfeit certification badge
    w_draw.rectangle([pw * 0.05, ph * 0.05, pw * 0.45, ph * 0.25], fill=(255, 230, 0), outline=(255, 0, 0), width=3)
    w_draw.text((pw * 0.08, ph * 0.08), "100% CERTIFIED", fill=(0, 0, 0))
    w_draw.text((pw * 0.08, ph * 0.15), "OFFICIAL DEALER", fill=(200, 0, 0))
    watch_img.save(spliced_prod_dir / "product_1.jpg", "JPEG", quality=85)
    
    shutil.copy(MERCHANTS_DIR / "suspicious" / "suspicious_logo.png", spliced_prod_dir / "logo.png")
    shutil.copy(MERCHANTS_DIR / "borderline" / "borderline_document.jpg", spliced_prod_dir / "document.jpg")
    (spliced_prod_dir / "meta.json").write_text(json.dumps({
        "name": "Aethelgard Chronometry",
        "category": "Luxury Timepieces",
        "claimed_brand": "Apex Brands",
        "ground_truth": "HIGH",
        "case_type": "manipulated_product_image",
        "ground_truth_risk_tier": "HIGH",
        "expected_evidence_summary": "Product imagery features spliced reference luxury watch with localized edge-gradient tampering and trademark mismatch.",
        "claims": {
            "inventory_claim": "Exclusive proprietary timepiece craftsmanship.",
            "brand_claim": "Official authorized flagship for Apex Brands.",
            "compliance_claim": "Statutory Ministry Incorporation Certificate."
        },
        "crawler_data": {
            "has_contact": True,
            "has_policy": True,
            "has_pricing": True,
            "has_about": False,
            "social_links": []
        }
    }, indent=2), encoding="utf-8")

    # Case E: Mixed Legitimate + Suspicious (susp_09_hybrid_boutique_counterfeit) -> Suspicious (HIGH)
    hybrid_dir = EVAL_ROOT / "suspicious" / "susp_09_hybrid_boutique_counterfeit"
    hybrid_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(EVAL_ROOT / "clean" / "clean_01_artisanal_terracotta" / "product_1.jpg", hybrid_dir / "product_1.jpg")
    shutil.copy(REF_DIR / "ref_handbag_leather.jpg", hybrid_dir / "product_2.jpg")
    shutil.copy(MERCHANTS_DIR / "suspicious" / "suspicious_logo.png", hybrid_dir / "logo.png")
    shutil.copy(MERCHANTS_DIR / "clean" / "clean_document.jpg", hybrid_dir / "document.jpg")
    (hybrid_dir / "meta.json").write_text(json.dumps({
        "name": "Atelier Heritage & Luxe Bazaar",
        "category": "Curated Designer Goods",
        "claimed_brand": "Luxe Atelier",
        "ground_truth": "HIGH",
        "case_type": "mixed_legitimate_suspicious",
        "ground_truth_risk_tier": "HIGH",
        "expected_evidence_summary": "Hybrid catalog contains mixed authentic artisanal items with unauthorized luxury brand reference matches and trademark logo divergence.",
        "claims": {
            "inventory_claim": "Curated blend of artisanal ceramics and exclusive designer luxury accessories.",
            "brand_claim": "Official regional partner for Luxe Atelier.",
            "compliance_claim": "Statutory Certificate of Incorporation."
        },
        "crawler_data": {
            "has_contact": True,
            "has_policy": True,
            "has_pricing": True,
            "has_about": True,
            "social_links": []
        }
    }, indent=2), encoding="utf-8")

    print("[OK] Extended test cases generated and existing metadata enriched successfully.")

if __name__ == "__main__":
    setup_extended_cases()
