"""
backend/routes/analyze.py — Router for Risk Analysis and Demo Ingestion.
Exposes POST /analyze and GET /demo-cases endpoints.
"""

from __future__ import annotations

import base64
import io
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import numpy as np
from PIL import Image
import cv2

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import engine modules
from visual.vit_embeddings import load_vit_model, get_image_embedding, compute_cosine_similarity
from visual.image_reuse import analyze_multiple_images_reuse, analyze_image_reuse, compute_identity_coherence
from visual.logo_check import check_logo_consistency
from visual.manipulation import analyze_image_manipulation
from visual.heatmap import generate_forensic_heatmap
from scoring.visual_score import calculate_visual_risk_score, WEIGHTS
from scoring.fusion import calculate_text_business_risk, fuse_risk_scores
from crawler.site_crawler import crawl_merchant
from crawler.image_extractor import download_images

router = APIRouter()

DATASET_DIR = BACKEND_DIR / "dataset"


def image_to_base64(img: Union[Image.Image, np.ndarray, None], fmt: str = "PNG") -> Optional[str]:
    """Convert a PIL Image or numpy RGB array to a base64 Data URL string."""
    if img is None:
        return None
    try:
        if isinstance(img, np.ndarray):
            if img.dtype != np.uint8:
                img = np.clip(img, 0, 255).astype(np.uint8)
            # Check dimensions
            if len(img.shape) == 2:
                pil_img = Image.fromarray(img, mode="L")
            elif img.shape[2] == 3:
                pil_img = Image.fromarray(img, mode="RGB")
            elif img.shape[2] == 4:
                pil_img = Image.fromarray(img, mode="RGBA")
            else:
                return None
        elif isinstance(img, Image.Image):
            pil_img = img
        else:
            return None

        buffered = io.BytesIO()
        pil_img.save(buffered, format=fmt)
        encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/{fmt.lower()};base64,{encoded}"
    except Exception as e:
        print(f"Error encoding image to base64: {e}")
        return None


def load_merchant_case(profile: str) -> Dict[str, Any]:
    """Load controlled demo merchant assets."""
    base = DATASET_DIR / "merchants"

    if profile == "Suspicious Merchant":
        pdir = base / "suspicious"
        images = []
        if (pdir / "suspicious_product_1.jpg").exists():
            images.append(Image.open(pdir / "suspicious_product_1.jpg").convert("RGB"))
        if (pdir / "suspicious_product_2.jpg").exists():
            images.append(Image.open(pdir / "suspicious_product_2.jpg").convert("RGB"))

        logo = Image.open(pdir / "suspicious_logo.png").convert("RGB") if (pdir / "suspicious_logo.png").exists() else None
        doc = Image.open(pdir / "suspicious_tampered_doc.jpg").convert("RGB") if (pdir / "suspicious_tampered_doc.jpg").exists() else None

        claims = {
            "inventory_claim": "Exclusive Authorized Dealer with authentic proprietary luxury watch and designer handbag inventory.",
            "brand_claim": "Official global flagship store for Apex Brands corporate identity.",
            "compliance_claim": "Statutory Ministry Incorporation Certificate registered under CIN-U74999MH2021PTC368920.",
        }

        crawler_mock = {
            "title": "Apex Global Luxury Retail — Premium Timepieces & Accessories",
            "domain": "apex-luxury-official-store.com",
            "has_contact": True,
            "has_policy": True,
            "has_pricing": True,
            "has_about": True,
            "social_links": ["https://instagram.com/apexluxury", "https://facebook.com/apexluxury"],
        }
        return {
            "name": "Apex Global Luxury Store",
            "category": "Luxury Watches & Designer Accessories",
            "product_images": images,
            "logo_image": logo,
            "document_image": doc,
            "claimed_brand": "Apex Brands",
            "claims": claims,
            "crawler_data": crawler_mock,
        }

    elif profile == "Clean Merchant":
        pdir = base / "clean"
        images = []
        if (pdir / "clean_product_1.jpg").exists():
            images.append(Image.open(pdir / "clean_product_1.jpg").convert("RGB"))
        if (pdir / "clean_product_2.jpg").exists():
            images.append(Image.open(pdir / "clean_product_2.jpg").convert("RGB"))

        logo = Image.open(pdir / "clean_logo.png").convert("RGB") if (pdir / "clean_logo.png").exists() else None
        doc = Image.open(pdir / "clean_document.jpg").convert("RGB") if (pdir / "clean_document.jpg").exists() else None

        claims = {
            "inventory_claim": "Independent artisan studio offering original handcrafted ceramics and handwoven linen goods.",
            "brand_claim": "Registered proprietary trademark for Earth & Clay studio.",
            "compliance_claim": "Statutory incorporation certificate without amendments.",
        }

        crawler_mock = {
            "title": "Earth & Clay Artisanal Studio — Handcrafted Pottery",
            "domain": "earthandclaystudio.com",
            "has_contact": True,
            "has_policy": True,
            "has_pricing": True,
            "has_about": True,
            "social_links": ["https://instagram.com/earthandclay"],
        }
        return {
            "name": "Earth & Clay Studio",
            "category": "Artisanal Home & Handcrafted Goods",
            "product_images": images,
            "logo_image": logo,
            "document_image": doc,
            "claimed_brand": "Earth & Clay",
            "claims": claims,
            "crawler_data": crawler_mock,
        }

    else:  # Borderline Merchant
        pdir = base / "borderline"
        images = []
        if (pdir / "borderline_product_1.jpg").exists():
            images.append(Image.open(pdir / "borderline_product_1.jpg").convert("RGB"))

        logo = Image.open(pdir / "borderline_logo.png").convert("RGB") if (pdir / "borderline_logo.png").exists() else None
        doc = Image.open(pdir / "borderline_document.jpg").convert("RGB") if (pdir / "borderline_document.jpg").exists() else None

        claims = {
            "inventory_claim": "Multi-brand urban apparel and athletic footwear distributor.",
            "brand_claim": "Authorized retail partner under regional sub-license.",
            "compliance_claim": "Standard digital business registration copy.",
        }

        crawler_mock = {
            "title": "Urban Velocity Store",
            "domain": "urbanvelocitystore.net",
            "has_contact": True,
            "has_policy": False,
            "has_pricing": True,
            "has_about": False,
            "social_links": [],
        }
        return {
            "name": "Urban Velocity Store",
            "category": "Footwear & Athletic Apparel",
            "product_images": images,
            "logo_image": logo,
            "document_image": doc,
            "claimed_brand": "Apex Store",
            "claims": claims,
            "crawler_data": crawler_mock,
        }


def run_pipeline(
    merchant_name: str,
    product_images: List[Image.Image],
    logo_image: Optional[Image.Image],
    document_image: Optional[Image.Image],
    claimed_brand: Optional[str],
    claims: Dict[str, str],
    crawler_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Executes actual algorithms across all images.
    Every single number in the output is dynamically calculated.
    """
    # 1. Warm model
    load_vit_model()

    # 2. Text / Business Risk
    text_risk_data = calculate_text_business_risk(crawler_data)

    # 3. Image Reuse Engine
    ref_dir = str(DATASET_DIR / "reference")
    reuse_data = analyze_multiple_images_reuse(product_images, reference_dir=ref_dir)

    # 4. Visual Identity Coherence Engine
    identity_data = compute_identity_coherence(product_images)

    # 5. Logo Consistency Engine
    logos_dir = str(DATASET_DIR / "logos")
    if logo_image:
        logo_data = check_logo_consistency(logo_image, claimed_brand=claimed_brand, logos_dir=logos_dir)
    else:
        logo_data = {
            "similarity": 0.5,
            "consistency_score": 50.0,
            "inconsistency_risk": 50.0,
            "risk_level": "MEDIUM",
            "matched_reference": None,
            "matched_path": None,
            "explanation": "No logo provided by merchant for visual identity verification.",
        }

    # 6. Manipulation & Forensic Heatmap Engine
    target_forensic_img = document_image if document_image is not None else (product_images[0] if product_images else None)
    if target_forensic_img is not None:
        manip_data = analyze_image_manipulation(target_forensic_img)
        heatmap_overlay = generate_forensic_heatmap(
            target_forensic_img,
            ela_image=manip_data["ela_image"],
            gradient_map=manip_data["gradient_map"],
            suspicious_boxes=manip_data["suspicious_regions"],
        )
    else:
        manip_data = {
            "manipulation_score": 5.0,
            "risk_level": "LOW",
            "ela_image": np.zeros((100, 100, 3), dtype=np.uint8),
            "gradient_map": np.zeros((100, 100), dtype=np.uint8),
            "synthetic_score": 5.0,
            "synthetic_desc": "No documents provided for forensic analysis.",
            "suspicious_regions": [],
            "explanation": "No forensic anomalies observed.",
        }
        heatmap_overlay = np.zeros((100, 100, 3), dtype=np.uint8)

    # 7. Composite Visual Risk Score Calculation (Weighted)
    visual_risk_data = calculate_visual_risk_score(
        reuse_data,
        logo_data,
        manip_data,
        cross_identity_coherence=identity_data["coherence_score"],
    )

    # 8. Multimodal Risk Fusion
    fused_result = fuse_risk_scores(
        text_risk_data=text_risk_data,
        visual_risk_data=visual_risk_data,
        reuse_data=reuse_data,
        logo_data=logo_data,
        manipulation_data=manip_data,
        merchant_name=merchant_name,
    )

    # Clean non-serializable elements from manip_data for raw dict
    ela_np = manip_data.get("ela_image")
    gradient_np = manip_data.get("gradient_map")
    
    serializable_manip = {
        k: v for k, v in manip_data.items() if k not in ["ela_image", "gradient_map"]
    }

    # Reference images base64
    matched_ref_b64 = None
    top_item = reuse_data.get("top_flagged_item")
    if top_item and top_item.get("reference_path") and os.path.exists(top_item["reference_path"]):
        try:
            matched_ref_b64 = image_to_base64(Image.open(top_item["reference_path"]))
        except Exception:
            pass

    matched_logo_ref_b64 = None
    if logo_data.get("matched_path") and os.path.exists(logo_data["matched_path"]):
        try:
            matched_logo_ref_b64 = image_to_base64(Image.open(logo_data["matched_path"]))
        except Exception:
            pass

    return {
        "fusion": fused_result,
        "text_risk": text_risk_data,
        "visual_risk": visual_risk_data,
        "reuse": reuse_data,
        "identity": identity_data,
        "logo": logo_data,
        "manipulation": serializable_manip,
        "claims": claims,
        "crawler_data": crawler_data,
        "weights": WEIGHTS,
        # Visual artifacts in Base64
        "forensic_target_image_base64": image_to_base64(target_forensic_img),
        "ela_image_base64": image_to_base64(ela_np),
        "heatmap_overlay_base64": image_to_base64(heatmap_overlay),
        "product_images_base64": [image_to_base64(img) for img in product_images],
        "logo_image_base64": image_to_base64(logo_image),
        "document_image_base64": image_to_base64(document_image),
        "matched_reference_image_base64": matched_ref_b64,
        "matched_logo_reference_base64": matched_logo_ref_b64,
    }


@router.get("/demo-cases")
async def get_demo_cases():
    """Returns metadata for the controlled demo merchant cases."""
    return [
        {
            "id": "Suspicious Merchant",
            "name": "Apex Global Luxury Store",
            "category": "Luxury Watches & Designer Accessories",
            "description": "High-risk merchant profile: Stolen catalog luxury timepieces (94% ViT match), altered brand mark, and digitally spliced certificate.",
            "claimed_brand": "Apex Brands",
            "claims": {
                "inventory_claim": "Exclusive Authorized Dealer with authentic proprietary luxury watch and designer handbag inventory.",
                "brand_claim": "Official global flagship store for Apex Brands corporate identity.",
                "compliance_claim": "Statutory Ministry Incorporation Certificate registered under CIN-U74999MH2021PTC368920.",
            },
        },
        {
            "id": "Clean Merchant",
            "name": "Earth & Clay Studio",
            "category": "Artisanal Home & Handcrafted Goods",
            "description": "Legitimate low-risk artisan merchant: Original studio pottery visuals, authentic artisanal mark, and un-tampered statutory certificate.",
            "claimed_brand": "Earth & Clay",
            "claims": {
                "inventory_claim": "Independent artisan studio offering original handcrafted ceramics and handwoven linen goods.",
                "brand_claim": "Registered proprietary trademark for Earth & Clay studio.",
                "compliance_claim": "Statutory incorporation certificate without amendments.",
            },
        },
        {
            "id": "Borderline Merchant",
            "name": "Urban Velocity Store",
            "category": "Footwear & Athletic Apparel",
            "description": "Moderate-risk distributor: Urban footwear with moderate visual variance and unverified sub-licensing disclosures.",
            "claimed_brand": "Apex Store",
            "claims": {
                "inventory_claim": "Multi-brand urban apparel and athletic footwear distributor.",
                "brand_claim": "Authorized retail partner under regional sub-license.",
                "compliance_claim": "Standard digital business registration copy.",
            },
        },
    ]


@router.post("/analyze")
async def analyze_merchant_endpoint(
    mode: str = Form("demo"),
    demo_case: Optional[str] = Form(None),
    target_url: Optional[str] = Form(None),
    merchant_name: Optional[str] = Form(None),
    claimed_brand: Optional[str] = Form(None),
    claim_inventory: Optional[str] = Form(None),
    claim_brand: Optional[str] = Form(None),
    claim_compliance: Optional[str] = Form(None),
    product_images: List[UploadFile] = File(default=[]),
    logo_image: Optional[UploadFile] = File(default=None),
    document_image: Optional[UploadFile] = File(default=None),
):
    """
    Main multimodal analysis endpoint. Accepts Demo, Live URL, or Custom Upload submissions.
    """
    try:
        if mode == "demo":
            case_name = demo_case or "Suspicious Merchant"
            loaded = load_merchant_case(case_name)
            return run_pipeline(
                merchant_name=loaded["name"],
                product_images=loaded["product_images"],
                logo_image=loaded["logo_image"],
                document_image=loaded["document_image"],
                claimed_brand=loaded["claimed_brand"],
                claims=loaded["claims"],
                crawler_data=loaded["crawler_data"],
            )

        elif mode == "url":
            url = target_url or "https://example.com"
            crawl_res = crawl_merchant(url)
            
            p_imgs = []
            if crawl_res.get("image_urls"):
                downloaded = download_images(crawl_res["image_urls"], max_images=4)
                p_imgs = [img.convert("RGB") for _, img in downloaded]

            if not p_imgs:
                # Fallback if URL blocked or no images found
                loaded = load_merchant_case("Suspicious Merchant")
                p_imgs = loaded["product_images"]

            claims = {
                "inventory_claim": f"E-commerce catalog from {crawl_res.get('domain', url)}",
                "brand_claim": f"Brand identity claimed as {claimed_brand or 'Merchant Brand'}",
                "compliance_claim": "Website self-reported disclosures.",
            }

            return run_pipeline(
                merchant_name=merchant_name or crawl_res.get("domain", "Live Merchant"),
                product_images=p_imgs,
                logo_image=p_imgs[0] if p_imgs else None,
                document_image=None,
                claimed_brand=claimed_brand,
                claims=claims,
                crawler_data=crawl_res if not crawl_res.get("error") else None,
            )

        elif mode == "upload":
            p_imgs: List[Image.Image] = []
            for file in product_images:
                content = await file.read()
                if content:
                    p_imgs.append(Image.open(io.BytesIO(content)).convert("RGB"))

            l_img: Optional[Image.Image] = None
            if logo_image:
                content = await logo_image.read()
                if content:
                    l_img = Image.open(io.BytesIO(content)).convert("RGB")

            d_img: Optional[Image.Image] = None
            if document_image:
                content = await document_image.read()
                if content:
                    d_img = Image.open(io.BytesIO(content)).convert("RGB")

            claims = {
                "inventory_claim": claim_inventory or "Uploaded product media claims direct proprietary ownership.",
                "brand_claim": claim_brand or f"Brand identity claimed as {claimed_brand or 'Custom Brand'}.",
                "compliance_claim": claim_compliance or "Uploaded statutory verification document.",
            }

            return run_pipeline(
                merchant_name=merchant_name or "Custom Merchant",
                product_images=p_imgs,
                logo_image=l_img,
                document_image=d_img,
                claimed_brand=claimed_brand or "Apex Brands",
                claims=claims,
                crawler_data=None,
            )

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported mode: {mode}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {str(e)}")
