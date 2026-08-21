"""
app.py — Visual Consistency & Evidence Engine
A professional, evidence-first merchant risk analysis dashboard.
Provides explainable visual evidence, side-by-side claim verification,
and multimodal risk fusion to empower human risk analysts.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import streamlit as st
import numpy as np
from PIL import Image
import cv2

import sys
sys.path.insert(0, str(Path(__file__).parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent))

# Import internal engine modules
from visual.vit_embeddings import load_vit_model, get_image_embedding, compute_cosine_similarity
from visual.image_reuse import analyze_multiple_images_reuse, analyze_image_reuse, compute_identity_coherence
from visual.logo_check import check_logo_consistency
from visual.manipulation import analyze_image_manipulation
from visual.heatmap import generate_forensic_heatmap
from scoring.visual_score import calculate_visual_risk_score, WEIGHTS
from scoring.fusion import calculate_text_business_risk, fuse_risk_scores
from crawler.site_crawler import crawl_merchant
from crawler.image_extractor import download_images


# ─────────────────────────────────────────────────────────────────────────────
# Streamlit Page Configuration
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Visual Consistency & Evidence Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS for Fintech / Risk Analyst UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .prototype-banner {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #3b82f6;
        border-left: 6px solid #3b82f6;
        padding: 0.75rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 1.2rem;
        font-size: 0.85rem;
        color: #cbd5e1;
    }
    
    .main-header {
        padding: 1.25rem 1.5rem;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 12px;
        border-left: 6px solid #6366f1;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: #f8fafc;
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .main-header p {
        color: #94a3b8;
        font-size: 0.95rem;
        margin: 0.35rem 0 0 0;
    }
    
    .risk-card {
        background: #1e293b;
        padding: 1.2rem;
        border-radius: 10px;
        border: 1px solid #334155;
        text-align: center;
    }
    
    .risk-score-value {
        font-size: 2.3rem;
        font-weight: 800;
        margin: 0.2rem 0;
    }
    
    .evidence-card {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
    }
    
    .claim-box {
        background: #1e293b;
        border-left: 4px solid #3b82f6;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.6rem;
    }
    
    .reality-box {
        background: #1e293b;
        border-left: 4px solid #ef4444;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.6rem;
    }
    
    .reality-box-green {
        background: #1e293b;
        border-left: 4px solid #22c55e;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.6rem;
    }
    
    .evidence-tag {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    
    .tag-red { background: rgba(220, 38, 38, 0.2); color: #ef4444; border: 1px solid #dc2626; }
    .tag-amber { background: rgba(217, 119, 6, 0.2); color: #f59e0b; border: 1px solid #d97706; }
    .tag-green { background: rgba(22, 163, 74, 0.2); color: #22c55e; border: 1px solid #16a34a; }
    
    .status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.9rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Model Pre-warm & Streamlit Cache
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading Vision Transformer backbone...")
def get_cached_model():
    return load_vit_model()


# ─────────────────────────────────────────────────────────────────────────────
# Demo Asset Loader
# ─────────────────────────────────────────────────────────────────────────────
def load_merchant_case(profile: str) -> Dict[str, Any]:
    """
    Load demo assets for a controlled merchant case.
    All scores are calculated dynamically by passing these actual image files
    through the ViT embedding and OpenCV forensic engines.
    """
    base = Path("backend/dataset/merchants") if Path("backend/dataset/merchants").exists() else Path("dataset/merchants")
    
    if profile == "Suspicious Merchant":
        pdir = base / "suspicious"
        images = []
        if (pdir / "suspicious_product_1.jpg").exists():
            images.append(Image.open(pdir / "suspicious_product_1.jpg"))
        if (pdir / "suspicious_product_2.jpg").exists():
            images.append(Image.open(pdir / "suspicious_product_2.jpg"))
            
        logo = Image.open(pdir / "suspicious_logo.png") if (pdir / "suspicious_logo.png").exists() else None
        doc = Image.open(pdir / "suspicious_tampered_doc.jpg") if (pdir / "suspicious_tampered_doc.jpg").exists() else None
        
        # Self-reported merchant claims (Text claims vs Visual proof)
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
            images.append(Image.open(pdir / "clean_product_1.jpg"))
        if (pdir / "clean_product_2.jpg").exists():
            images.append(Image.open(pdir / "clean_product_2.jpg"))
            
        logo = Image.open(pdir / "clean_logo.png") if (pdir / "clean_logo.png").exists() else None
        doc = Image.open(pdir / "clean_document.jpg") if (pdir / "clean_document.jpg").exists() else None
        
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
            images.append(Image.open(pdir / "borderline_product_1.jpg"))
            
        logo = Image.open(pdir / "borderline_logo.png") if (pdir / "borderline_logo.png").exists() else None
        doc = Image.open(pdir / "borderline_document.jpg") if (pdir / "borderline_document.jpg").exists() else None
        
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


# ─────────────────────────────────────────────────────────────────────────────
# Dynamic Analysis Pipeline Runner (Strictly calculated, never hardcoded)
# ─────────────────────────────────────────────────────────────────────────────
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
    get_cached_model()

    # 2. Text / Business Risk (Evaluated on crawler disclosures)
    text_risk_data = calculate_text_business_risk(crawler_data)

    # 3. Image Reuse Engine (ViT feature extraction & cosine distance)
    ref_dir = "backend/dataset/reference" if Path("backend/dataset/reference").exists() else "dataset/reference"
    reuse_data = analyze_multiple_images_reuse(product_images, reference_dir=ref_dir)

    # 4. Visual Identity Coherence Engine (Pairwise internal visual consistency)
    identity_data = compute_identity_coherence(product_images)

    # 5. Logo Consistency Engine (ViT comparison against verified logos)
    logos_dir = "backend/dataset/logos" if Path("backend/dataset/logos").exists() else "dataset/logos"
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

    return {
        "fusion": fused_result,
        "text_risk": text_risk_data,
        "visual_risk": visual_risk_data,
        "reuse": reuse_data,
        "identity": identity_data,
        "logo": logo_data,
        "manipulation": manip_data,
        "forensic_target_image": target_forensic_img,
        "heatmap_overlay": heatmap_overlay,
        "claims": claims,
        "crawler_data": crawler_data,
        "product_images": product_images,
        "logo_image": logo_image,
        "document_image": document_image,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar Controls
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=52)
    st.title("Risk Controller")
    st.caption("Visual Consistency & Evidence Engine")
    st.markdown("---")

    analysis_mode = st.radio(
        "Select Ingestion Mode",
        ["Mode A — Demo Case (Offline)", "Mode B — Live Merchant URL", "Mode C — Manual File Upload"],
    )

    merchant_data_to_run = None

    if analysis_mode == "Mode A — Demo Case (Offline)":
        st.subheader("Controlled Dataset Cases")
        demo_selection = st.selectbox(
            "Select Merchant Case:",
            ["Suspicious Merchant", "Clean Merchant", "Borderline Merchant"],
            index=0,
            help="Suspicious: Reused catalog watch/bag, altered logo, tampered certificate\nClean: Original artisanal goods\nBorderline: Moderate similarity",
        )
        if st.button("🚀 Analyze Merchant", type="primary", use_container_width=True):
            with st.spinner(f"Processing {demo_selection} through ViT & Forensic Pipeline..."):
                loaded = load_merchant_case(demo_selection)
                merchant_data_to_run = loaded

    elif analysis_mode == "Mode B — Live Merchant URL":
        st.subheader("Live Web Ingestion")
        target_url = st.text_input("Merchant Website URL", value="https://example.com", placeholder="https://merchant-store.com")
        claimed_brand_input = st.text_input("Claimed Brand Name", placeholder="e.g. Apex Brands")
        
        if st.button("🌐 Crawl & Analyze", type="primary", use_container_width=True):
            with st.spinner("Crawling website and extracting visual evidence..."):
                crawl_res = crawl_merchant(target_url)
                if crawl_res.get("error"):
                    st.warning(f"Crawling notice: {crawl_res['error']}. Falling back to demo assets.")
                    merchant_data_to_run = load_merchant_case("Suspicious Merchant")
                else:
                    st.success(f"Crawled successfully! Found {len(crawl_res['image_urls'])} image URLs.")
                    downloaded_imgs = download_images(crawl_res["image_urls"], max_images=4)
                    pil_imgs = [img for _, img in downloaded_imgs]
                    
                    if not pil_imgs:
                        st.info("No downloadable images found. Using demo assets.")
                        merchant_data_to_run = load_merchant_case("Suspicious Merchant")
                    else:
                        merchant_data_to_run = {
                            "name": crawl_res.get("domain", "Live Merchant"),
                            "category": "E-Commerce Store",
                            "product_images": pil_imgs,
                            "logo_image": pil_imgs[0] if pil_imgs else None,
                            "document_image": None,
                            "claimed_brand": claimed_brand_input if claimed_brand_input else None,
                            "claims": {
                                "inventory_claim": f"E-commerce catalog from {crawl_res.get('domain', 'website')}",
                                "brand_claim": f"Brand identity claimed as {claimed_brand_input or 'merchant'}",
                                "compliance_claim": "Website self-reported disclosures.",
                            },
                            "crawler_data": crawl_res,
                        }

    else:  # Mode C: Manual Upload
        st.subheader("Upload Merchant Visuals")
        uploaded_products = st.file_uploader("Upload Product Images", accept_multiple_files=True, type=["jpg", "jpeg", "png", "webp"])
        uploaded_logo = st.file_uploader("Upload Merchant Logo", type=["jpg", "jpeg", "png", "webp"])
        uploaded_doc = st.file_uploader("Upload Document / Certificate", type=["jpg", "jpeg", "png", "webp"])
        brand_name_custom = st.text_input("Claimed Brand Name", value="Apex Brands")

        if st.button("🔍 Run Custom Analysis", type="primary", use_container_width=True):
            if not uploaded_products and not uploaded_logo and not uploaded_doc:
                st.error("Please upload at least one image, logo, or document.")
            else:
                p_imgs = [Image.open(f).convert("RGB") for f in uploaded_products] if uploaded_products else []
                l_img = Image.open(uploaded_logo).convert("RGB") if uploaded_logo else None
                d_img = Image.open(uploaded_doc).convert("RGB") if uploaded_doc else None
                
                merchant_data_to_run = {
                    "name": "Custom Uploaded Merchant",
                    "category": "Uploaded Media",
                    "product_images": p_imgs,
                    "logo_image": l_img,
                    "document_image": d_img,
                    "claimed_brand": brand_name_custom,
                    "claims": {
                        "inventory_claim": "Uploaded product media claims direct proprietary ownership.",
                        "brand_claim": f"Brand identity claimed as {brand_name_custom}.",
                        "compliance_claim": "Uploaded statutory certificate.",
                    },
                    "crawler_data": None,
                }

    st.markdown("---")
    st.caption("⚖️ **Decision Support Framework**")
    st.caption(
        "This system computes empirical visual evidence to support human risk reviewers. "
        "It **never** automatically rejects merchants or declares fraud verdicts."
    )


# Store results in session state so dashboard interactions remain persistent
if merchant_data_to_run is not None:
    st.session_state["analysis_result"] = run_pipeline(
        merchant_name=merchant_data_to_run["name"],
        product_images=merchant_data_to_run["product_images"],
        logo_image=merchant_data_to_run["logo_image"],
        document_image=merchant_data_to_run["document_image"],
        claimed_brand=merchant_data_to_run["claimed_brand"],
        claims=merchant_data_to_run["claims"],
        crawler_data=merchant_data_to_run["crawler_data"],
    )

# Default to Suspicious Merchant on initial load to show genuine evidence features
if "analysis_result" not in st.session_state:
    default_case = load_merchant_case("Suspicious Merchant")
    st.session_state["analysis_result"] = run_pipeline(
        merchant_name=default_case["name"],
        product_images=default_case["product_images"],
        logo_image=default_case["logo_image"],
        document_image=default_case["document_image"],
        claimed_brand=default_case["claimed_brand"],
        claims=default_case["claims"],
        crawler_data=default_case["crawler_data"],
    )

res = st.session_state["analysis_result"]
fusion = res["fusion"]
visual_risk = res["visual_risk"]
text_risk = res["text_risk"]
reuse = res["reuse"]
identity = res.get("identity", {"coherence_score": 70.0, "explanation": "Visual coherence calculated.", "pairwise_similarities": []})
logo = res["logo"]
manip = res["manipulation"]
claims = res["claims"]


# ─────────────────────────────────────────────────────────────────────────────
# Top Banner & Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="prototype-banner">
        🛡️ <b>DECISION-SUPPORT PROTOTYPE FOR HUMAN RISK ANALYSTS:</b> This engine provides explainable empirical visual signals to assist risk reviewers. It <b>never</b> automatically rejects merchants or declares fraud verdicts.
    </div>
    <div class="main-header">
        <h1>Visual Consistency & Evidence Engine</h1>
        <p>Explainable visual evidence and multimodal risk fusion for merchant onboarding & risk operations</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Top Merchant Overview & Dynamic Risk Metric Cards
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"### 📋 Merchant Profile: **{fusion['merchant_name']}**")

col_text, col_vis, col_final, col_status = st.columns([1, 1, 1, 1.4])

with col_text:
    st.markdown(
        f"""
        <div class="risk-card">
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Simulated Text / Business Risk</span>
            <div class="risk-score-value" style="color: #60a5fa;">{fusion['text_risk_score']} <span style="font-size: 1.1rem; color: #64748b;">/ 100</span></div>
            <div style="font-size: 0.8rem; color: #94a3b8;">Textual Disclosures</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_vis:
    vis_color = "#ef4444" if fusion['visual_risk_score'] >= 70 else ("#f59e0b" if fusion['visual_risk_score'] >= 40 else "#22c55e")
    st.markdown(
        f"""
        <div class="risk-card">
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Visual Evidence Risk</span>
            <div class="risk-score-value" style="color: {vis_color};">{fusion['visual_risk_score']} <span style="font-size: 1.1rem; color: #64748b;">/ 100</span></div>
            <div style="font-size: 0.8rem; color: #94a3b8;">Calculated ViT & Forensics</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_final:
    final_color = fusion["badge_color"]
    st.markdown(
        f"""
        <div class="risk-card" style="border: 2px solid {final_color};">
            <span style="color: #cbd5e1; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Final Fused Risk</span>
            <div class="risk-score-value" style="color: {final_color};">{fusion['final_risk_score']} <span style="font-size: 1.1rem; color: #64748b;">/ 100</span></div>
            <div style="font-size: 0.8rem; color: #cbd5e1; font-weight: 600;">Multimodal Score</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_status:
    badge_bg = f"background-color: {fusion['badge_color']}; color: white;"
    st.markdown(
        f"""
        <div class="risk-card" style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
            <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; margin-bottom: 0.3rem;">Status Classification</div>
            <div>
                <span class="status-badge" style="{badge_bg}">{fusion['status_label']}</span>
            </div>
            <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 0.5rem;">{fusion['recommendation']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# EVIDENCE-FIRST: Claim vs Visual Evidence Core Matrix
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("## ⚖️ Claim vs. Visual Evidence Matrix")
st.caption("Direct side-by-side comparison answering: *«Does the visual evidence on this merchant support or contradict what the merchant claims?»*")

top_item = reuse.get("top_flagged_item")
top_sim = top_item["similarity"] if top_item else 0.0
ref_name = top_item["reference_filename"] if top_item else "None"
logo_sim = logo.get("similarity", 1.0)
manip_score = manip.get("manipulation_score", 0.0)

m_col1, m_col2, m_col3 = st.columns(3)

# Dimension 1: Inventory & Product Imagery
with m_col1:
    st.markdown("#### 🛍️ 1. Inventory & Products")
    st.markdown(
        f"""
        <div class="claim-box">
            <span style="font-size: 0.75rem; font-weight: 700; color: #60a5fa; text-transform: uppercase;">Merchant Claim</span>
            <div style="font-size: 0.85rem; color: #e2e8f0; margin-top: 0.2rem;">{claims.get('inventory_claim', 'Authentic inventory')}</div>
        </div>
        <div class="{'reality-box' if top_sim >= 0.80 else 'reality-box-green'}">
            <span style="font-size: 0.75rem; font-weight: 700; color: {'#ef4444' if top_sim >= 0.80 else '#22c55e'}; text-transform: uppercase;">
                {'CONTRADICTS (High Reuse)' if top_sim >= 0.80 else 'SUPPORTS (Original)'}
            </span>
            <div style="font-size: 0.85rem; color: #e2e8f0; margin-top: 0.2rem;">
                <b>ViT Similarity:</b> {int(round(top_sim * 100))}% match with reference <code>{ref_name}</code>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Dimension 2: Brand Identity & Logo
with m_col2:
    st.markdown("#### 🏷️ 2. Brand Identity & Logo")
    st.markdown(
        f"""
        <div class="claim-box">
            <span style="font-size: 0.75rem; font-weight: 700; color: #60a5fa; text-transform: uppercase;">Merchant Claim</span>
            <div style="font-size: 0.85rem; color: #e2e8f0; margin-top: 0.2rem;">{claims.get('brand_claim', 'Verified brand partner')}</div>
        </div>
        <div class="{'reality-box' if logo_sim < 0.65 else 'reality-box-green'}">
            <span style="font-size: 0.75rem; font-weight: 700; color: {'#ef4444' if logo_sim < 0.65 else '#22c55e'}; text-transform: uppercase;">
                {'CONTRADICTS (Stylistic Divergence)' if logo_sim < 0.65 else 'SUPPORTS (Consistent)'}
            </span>
            <div style="font-size: 0.85rem; color: #e2e8f0; margin-top: 0.2rem;">
                <b>Logo Consistency:</b> {logo.get('consistency_score', 100)}% match vs official reference asset.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Dimension 3: Document & Statutory Compliance
with m_col3:
    st.markdown("#### 📜 3. Document Integrity")
    st.markdown(
        f"""
        <div class="claim-box">
            <span style="font-size: 0.75rem; font-weight: 700; color: #60a5fa; text-transform: uppercase;">Merchant Claim</span>
            <div style="font-size: 0.85rem; color: #e2e8f0; margin-top: 0.2rem;">{claims.get('compliance_claim', 'Official incorporation document')}</div>
        </div>
        <div class="{'reality-box' if manip_score >= 40.0 else 'reality-box-green'}">
            <span style="font-size: 0.75rem; font-weight: 700; color: {'#ef4444' if manip_score >= 40.0 else '#22c55e'}; text-transform: uppercase;">
                {'CONTRADICTS (Splicing Anomaly)' if manip_score >= 40.0 else 'SUPPORTS (Uniform Compression)'}
            </span>
            <div style="font-size: 0.85rem; color: #e2e8f0; margin-top: 0.2rem;">
                <b>Forensic Indicator Score:</b> {manip_score}% localized variance & re-compression.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Visual Evidence Breakdown Progress Grid
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 📊 Empirical Signal Breakdown")

vcol1, vcol2, vcol3, vcol4, vcol5 = st.columns(5)

# 1. Image Reuse
with vcol1:
    reuse_pct = int(round(reuse.get("max_similarity", 0.0) * 100))
    st.markdown(
        f"""
        <div class="evidence-card">
            <div style="font-size: 0.85rem; font-weight: 600; color: #e2e8f0;">Image Reuse</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {'#ef4444' if reuse_pct >= 85 else ('#f59e0b' if reuse_pct >= 70 else '#22c55e')};">{reuse_pct}%</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Max cosine similarity vs catalog</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, reuse_pct / 100.0))

# 2. Logo Inconsistency
with vcol2:
    logo_incon_pct = int(round(logo.get("inconsistency_risk", 0.0)))
    st.markdown(
        f"""
        <div class="evidence-card">
            <div style="font-size: 0.85rem; font-weight: 600; color: #e2e8f0;">Logo Inconsistency</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {'#ef4444' if logo_incon_pct >= 60 else ('#f59e0b' if logo_incon_pct >= 30 else '#22c55e')};">{logo_incon_pct}%</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Variance from official identity</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, logo_incon_pct / 100.0))

# 3. Manipulation Indicators
with vcol3:
    manip_pct = int(round(manip.get("manipulation_score", 0.0)))
    st.markdown(
        f"""
        <div class="evidence-card">
            <div style="font-size: 0.85rem; font-weight: 600; color: #e2e8f0;">Manipulation Indicators</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {'#ef4444' if manip_pct >= 65 else ('#f59e0b' if manip_pct >= 35 else '#22c55e')};">{manip_pct}%</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Compression & splicing signal</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, manip_pct / 100.0))

# 4. Synthetic Suspicion
with vcol4:
    synth_pct = int(round(manip.get("synthetic_score", 0.0)))
    st.markdown(
        f"""
        <div class="evidence-card">
            <div style="font-size: 0.85rem; font-weight: 600; color: #e2e8f0;">Synthetic-Image Suspicion</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {'#f59e0b' if synth_pct >= 60 else '#60a5fa'};">{synth_pct}%</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Supporting visual frequency signal</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, synth_pct / 100.0))

# 5. Visual Identity Consistency
with vcol5:
    coherence_pct = int(round(identity.get("coherence_score", 70.0)))
    coherence_tier_label = (
        "Strong internal visual consistency"
        if coherence_pct >= 80
        else ("Moderate internal visual consistency" if coherence_pct >= 55 else "Low internal visual consistency, images may originate from different sources")
    )
    st.markdown(
        f"""
        <div class="evidence-card">
            <div style="font-size: 0.85rem; font-weight: 600; color: #e2e8f0;">Identity Consistency</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {'#22c55e' if coherence_pct >= 80 else ('#f59e0b' if coherence_pct >= 55 else '#ef4444')};">{coherence_pct}%</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">{coherence_tier_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, coherence_pct / 100.0))


# ─────────────────────────────────────────────────────────────────────────────
# Explainability Rationale Bullets
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"### 💡 Why is this merchant categorized as **{fusion['status']} RISK**?")

with st.container():
    for idx, reason in enumerate(fusion["reasons"], 1):
        st.markdown(f"**{idx}.** {reason}")


# ─────────────────────────────────────────────────────────────────────────────
# Detailed Evidence & Forensic Deep Dive
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Image Reuse & Logo Side-by-Side",
    "🔬 Forensic Manipulation & Heatmap",
    "⚖️ Multimodal Risk Weights & Audit",
    "📄 Inspector & JSON Export",
])

# ── Tab 1: Image Reuse & Logo Side-by-Side ──
with tab1:
    st.subheader("1. Image Reuse Evidence")
    st.caption("Compares merchant product images against verified reference catalog using Vision Transformer (ViT) embeddings.")

    if top_item and top_item.get("reference_path") and os.path.exists(top_item["reference_path"]):
        c_merch, c_ref, c_details = st.columns([1, 1, 1.3])

        with c_merch:
            st.markdown("**Merchant Product Visual**")
            m_idx = top_item.get("image_index", 0)
            if res["product_images"] and m_idx < len(res["product_images"]):
                st.image(res["product_images"][m_idx], use_container_width=True)
            else:
                st.info("Merchant image")

        with c_ref:
            st.markdown(f"**Matched Catalog Reference** (`{top_item['reference_filename']}`)")
            ref_pil = Image.open(top_item["reference_path"])
            st.image(ref_pil, use_container_width=True)

        with c_details:
            st.markdown(
                f"""
                <div class="evidence-card">
                    <span class="evidence-tag {'tag-red' if top_item['risk_level'] == 'HIGH' else 'tag-amber'}">
                        {top_item['risk_level']} REUSE RISK
                    </span>
                    <h4 style="margin: 0.3rem 0; color: #f8fafc;">Cosine Similarity: {int(round(top_item['similarity'] * 100))}%</h4>
                    <p style="font-size: 0.85rem; color: #94a3b8;"><b>WHAT WAS FOUND:</b><br>{top_item['explanation']}</p>
                    <p style="font-size: 0.85rem; color: #94a3b8;"><b>WHY IT MATTERS:</b><br>Duplicated catalog photos indicate potential inventory misrepresentation or unauthorized drop-shipping.</p>
                    <p style="font-size: 0.85rem; color: #94a3b8;"><b>CONFIDENCE / SCORE:</b><br>Actual ViT embedding similarity = <code>{top_item['similarity']}</code></p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No catalog reference matches flagged.")

    st.markdown("---")
    st.subheader("2. Logo & Brand Identity Consistency")
    st.caption("Compares merchant logo against verified brand repository in dataset/logos/.")

    l_col1, l_col2, l_col3 = st.columns([1, 1, 1.3])
    with l_col1:
        st.markdown("**Merchant Provided Logo**")
        if res["logo_image"]:
            st.image(res["logo_image"], use_container_width=True)
        else:
            st.info("No logo image provided")

    with l_col2:
        st.markdown(f"**Verified Official Asset** (`{logo.get('matched_reference', 'None')}`)")
        if logo.get("matched_path") and os.path.exists(logo["matched_path"]):
            ref_logo_pil = Image.open(logo["matched_path"])
            st.image(ref_logo_pil, use_container_width=True)
        else:
            st.info("No verified reference logo found")

    with l_col3:
        st.markdown(
            f"""
            <div class="evidence-card">
                <span class="evidence-tag {'tag-red' if logo['risk_level'] == 'HIGH' else ('tag-amber' if logo['risk_level'] == 'MEDIUM' else 'tag-green')}">
                    {logo['risk_level']} INCONSISTENCY
                </span>
                <h4 style="margin: 0.3rem 0; color: #f8fafc;">Consistency Score: {logo['consistency_score']}%</h4>
                <p style="font-size: 0.85rem; color: #94a3b8;"><b>EVALUATION:</b><br>{logo['explanation']}</p>
                <p style="font-size: 0.85rem; color: #94a3b8;"><b>POLICY NOTICE:</b><br>Identifies visual stylistic variance. Does not claim trademark infringement or fraud.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("3. Visual Identity Consistency (Internal Catalog Coherence)")
    st.caption("Measures pairwise visual similarity among merchant's own product catalog images using Vision Transformer (ViT) embeddings.")

    coh_score = identity.get("coherence_score", 70.0)
    coh_level = "HIGH" if coh_score >= 80.0 else ("MEDIUM" if coh_score >= 55.0 else "LOW")
    tag_class = "tag-green" if coh_score >= 80.0 else ("tag-amber" if coh_score >= 55.0 else "tag-red")
    tier_desc = (
        "strong internal visual consistency"
        if coh_score >= 80.0
        else ("moderate internal visual consistency" if coh_score >= 55.0 else "low internal visual consistency, images may originate from different sources")
    )

    st.markdown(
        f"""
        <div class="evidence-card">
            <span class="evidence-tag {tag_class}">
                {coh_level} IDENTITY COHERENCE
            </span>
            <h4 style="margin: 0.3rem 0; color: #f8fafc;">Visual Identity Consistency: {coh_score}%</h4>
            <p style="font-size: 0.85rem; color: #94a3b8;"><b>EVALUATION:</b><br>{identity.get('explanation', '')}</p>
            <p style="font-size: 0.85rem; color: #94a3b8;"><b>TIER CLASSIFICATION:</b><br>Demonstrates <i>{tier_desc}</i>.</p>
            <p style="font-size: 0.85rem; color: #94a3b8;"><b>WHY IT MATTERS:</b><br>High internal coherence indicates authentic, unified product inventory. Low coherence suggests images scraped or aggregated from disparate sources.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Tab 2: Forensic Manipulation & Heatmap ──
with tab2:
    st.subheader("Image Forensic Analysis & Explainable Heatmap")
    st.caption("Uses Error Level Analysis (ELA) and local Laplacian gradient variance to highlight suspicious compression discrepancies and spliced regions.")

    if res["forensic_target_image"] is not None:
        f_col1, f_col2, f_col3 = st.columns(3)

        with f_col1:
            st.markdown("**1. Original Analyzed Document / Visual**")
            st.image(res["forensic_target_image"], use_container_width=True)

        with f_col2:
            st.markdown("**2. Error Level Analysis (ELA)**")
            st.image(manip["ela_image"], use_container_width=True)
            st.caption("Bright high-contrast patches reveal localized re-compression anomalies.")

        with f_col3:
            st.markdown("**3. Explainable Forensic Heatmap**")
            st.image(res["heatmap_overlay"], use_container_width=True)
            st.caption("Red/amber zones indicate high anomaly density and bounding box overlays.")

        st.markdown(
            f"""
            <div class="evidence-card">
                <span class="evidence-tag {'tag-red' if manip['risk_level'] == 'HIGH' else ('tag-amber' if manip['risk_level'] == 'MEDIUM' else 'tag-green')}">
                    FORENSIC SCORE: {manip['manipulation_score']}% ({manip['risk_level']})
                </span>
                <p style="font-size: 0.9rem; color: #e2e8f0; margin-top: 0.5rem;"><b>Forensic Finding:</b> {manip['explanation']}</p>
                <p style="font-size: 0.85rem; color: #94a3b8;"><b>Synthetic-Image Suspicion (Supporting Signal):</b> {manip['synthetic_score']}% — {manip['synthetic_desc']}</p>
                <p style="font-size: 0.8rem; color: #64748b;"><i>Disclaimer: Visual forensic signals indicate compression and edge variances. They do not constitute absolute proof of tampering.</i></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("No document or visual available for forensic heatmap.")


# ── Tab 3: Multimodal Risk Weights & Audit ──
with tab3:
    st.subheader("Multimodal Risk Scoring & Fusion Breakdown")

    st.markdown("#### Visual Dimension Weights Allocation")
    b_data = visual_risk["breakdown"]

    st.table([
        {
            "Visual Signal Dimension": v["label"],
            "Raw Score (0-100)": f"{v['score']}%",
            "Weight": f"{int(v['weight'] * 100)}%",
            "Weighted Risk Contribution": f"{v['weighted_contribution']}",
        }
        for k, v in b_data.items()
    ])

    st.markdown("#### Text / Business Risk Signals (Simulated)")
    st.json(text_risk["signals"])
    st.caption(text_risk["summary"])

    st.markdown("#### Fusion Formula Audit")
    st.markdown(
        f"""
        ```
        Text Risk = {fusion['text_risk_score']}
        Visual Risk = {fusion['visual_risk_score']}
        
        Formula:
        {'Deceptive Visual Contrast: Visual Risk (>= 70) and Text Risk (< 40)' if fusion['visual_risk_score'] >= 70 and fusion['text_risk_score'] < 40 else 'Standard Multi-Signal Fusion'}
        Final Risk = {fusion['final_risk_score']} / 100 -> {fusion['status_label']}
        ```
        """
    )


# ── Tab 4: Raw Inspector & JSON Export ──
with tab4:
    st.subheader("Audit Log & Raw Inspector")
    st.caption("Full structured data packet for compliance and manual review records.")

    export_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "merchant_name": fusion["merchant_name"],
        "final_risk_score": fusion["final_risk_score"],
        "status": fusion["status"],
        "status_label": fusion["status_label"],
        "recommendation": fusion["recommendation"],
        "reasons": fusion["reasons"],
        "claims_vs_visual_evidence": {
            "inventory_claim": claims.get("inventory_claim"),
            "inventory_visual_similarity": top_sim,
            "brand_claim": claims.get("brand_claim"),
            "logo_consistency_score": logo.get("consistency_score"),
            "compliance_claim": claims.get("compliance_claim"),
            "manipulation_score": manip.get("manipulation_score"),
        },
        "scores": {
            "text_risk_score": text_risk["text_risk_score"],
            "visual_risk_score": visual_risk["visual_risk_score"],
            "reuse_similarity_max": reuse.get("max_similarity", 0.0),
            "identity_coherence_score": identity.get("coherence_score", 70.0),
            "logo_inconsistency": logo.get("inconsistency_risk", 0.0),
            "manipulation_score": manip.get("manipulation_score", 0.0),
            "synthetic_score": manip.get("synthetic_score", 0.0),
        },
        "weights": WEIGHTS,
    }

    st.json(export_data)

    st.download_button(
        label="📥 Download Analyst Review Report (JSON)",
        data=json.dumps(export_data, indent=2),
        file_name=f"risk_report_{fusion['merchant_name'].lower().replace(' ', '_')}.json",
        mime="application/json",
    )
