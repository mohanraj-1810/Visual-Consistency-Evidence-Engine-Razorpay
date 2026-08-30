# 🛡️ Visual Consistency & Evidence Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![HuggingFace ViT](https://img.shields.io/badge/HuggingFace-ViT--Base-yellow.svg?logo=huggingface&logoColor=white)](https://huggingface.co/google/vit-base-patch16-224)
[![React](https://img.shields.io/badge/React-18.x-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.x-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Explainable visual evidence forensics and multimodal risk fusion for merchant onboarding, risk operations, and dispute intelligence.**

---

## 📑 Table of Contents

1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [Key Capabilities & Technical Highlights](#2-key-capabilities--technical-highlights)
3. [System Architecture](#3-system-architecture)
4. [Project Structure](#4-project-structure)
5. [Installation & Quickstart Guide](#5-installation--quickstart-guide)
6. [Interactive Frontend & Analyst Cockpit](#6-interactive-frontend--analyst-cockpit)
7. [API Reference & WebSocket Specs](#7-api-reference--websocket-specs)
8. [Evaluation, Testing & Benchmarking](#8-evaluation-testing--benchmarking)
9. [Operational Guidelines & Risk Scoring Model](#9-operational-guidelines--risk-scoring-model)
10. [Limitations & Future Roadmap](#10-limitations--future-roadmap)

---

## 1. Executive Summary & Problem Statement

Traditional merchant onboarding and automated risk screening systems predominantly rely on **textual disclosures**, self-reported business categories, government tax/statutory identifiers (e.g., GSTIN, CIN, PAN), and static web page parsing.

However, fraudulent entities, counterfeit storefronts, and high-risk merchants frequently circumvent text-based validations by:
- **Stealing Catalog Visuals:** Claiming proprietary luxury goods, bespoke electronics, or organic cosmetics while republishing stock photos or imagery scraped from established platforms (e.g., Amazon, Alibaba, Nike).
- **Brand Logo Distortion & Spoofing:** Displaying altered, distorted, or unauthorized registered trademarks to mislead consumers and underwriters.
- **Document & Invoice Tampering:** Submitting digitally altered incorporation certificates, bank statements, or wholesale invoices with localized text, font, or stamp splicing.
- **Visual Identity Dispersion:** Deploying disjointed, inconsistent imagery across a single storefront (e.g., mixing studio-grade catalog shots with low-resolution clip-art), indicating synthetic or aggregator dropshipping setups.

### The Solution
The **Visual Consistency & Evidence Engine** determines whether the visual artifacts provided or crawled from a merchant's digital storefront **empirically corroborate or contradict their business claims**. It translates raw pixel arrays into calibrated forensic evidence, similarity heatmaps, and multimodal risk scores to empower human risk underwriters.

---

## 2. Key Capabilities & Technical Highlights

```mermaid
flowchart LR
    A[Merchant Website / Uploads] --> B[SSRF-Safe Crawler]
    B --> C[Visual Ingestion & dHash Deduplication]
    C --> D[Pretrained ViT Backbone (768-d)]
    
    D --> E1[Catalog Reuse Detection]
    D --> E2[Logo Consistency & Brand Registry]
    D --> E3[Forensic ELA & Splicing Heatmap]
    D --> E4[Online Reverse Evidence Search]
    
    E1 & E2 & E3 & E4 --> F[Multimodal Risk Fusion Engine]
    F --> G[Analyst Cockpit & Real-Time Stream]
```

### 🧠 Pretrained Vision Transformer (ViT) Backbone
- Uses `google/vit-base-patch16-224` to compute dense, 768-dimensional L2-normalized semantic feature representations.
- Performs cosine similarity comparisons with sub-millisecond vector operations.
- Runs **100% offline at inference time**, requiring no external proprietary vision inference calls for core feature extraction.

### 🌐 SSRF-Hardened Web Crawler & Smart Asset Ingestion
- Automated headless crawling with strict **Server-Side Request Forgery (SSRF) protection** (blocks loopback, private RFC1918 subnets, and metadata endpoints).
- Intelligent asset filtering: eliminates UI glyphs, tracking pixels, favicons, and payment badges.
- Perceptual image deduplication using difference hashing (**dHash**) and Hamming distance clustering.
- Product-centric priority scoring (surfaces primary product imagery for inspection).

### 🔍 Forensic Manipulation & Heatmap Generation
- **Error Level Analysis (ELA):** Identifies localized compression discrepancies caused by resaving spliced JPEG segments at different quality matrices.
- **Laplacian High-Frequency Noise Analysis:** Highlights artificial edge artifacts from digital stamp splicing and text manipulation.
- **Explainable Anomaly Overlays:** Generates color-coded forensic heatmaps with automatically computed bounding boxes around suspicious regions.

### 🏷️ Brand & Logo Consistency Verification
- Compares claimed brand assets against registered reference brand libraries.
- Quantifies visual divergence and flags unauthorized or distorted trademark usage.

### 🛡️ Online Evidence Retrieval, Soft-Trust & Zero Penalty Safeguard
- Discovers external visual matches across e-commerce marketplaces and reference repositories.
- **Dual Evidence Separation (E1 vs. E4):**
  - **E1 (Local/Platform Index):** Evaluates near-duplicate cross-merchant image sharing across previously scanned live stores.
  - **E4 (External Web Candidate Evidence):** Queries Serper / public search engines, normalizes domain trust, and calibrates evidence confidence.
- **Soft-Trust & Supplier Catalog Handling:** Automatically identifies wholesale directories (Alibaba, IndiaMART, 1688) and social aggregators (Pinterest, Imgur, Flickr), mapping them to low evidence weight (`INSUFFICIENT_EVIDENCE`) to protect legitimate resellers and dropshippers from unfair high-risk penalties.
- **Zero Penalty Protection for Original/Artisanal Brands:** Prevents penalizing unique, proprietary photography that has no external matches.

### ⚖️ Multimodal Risk Fusion Engine & Corroboration Gate
- Combines visual reuse, logo divergence, forensic tampering, and text-visual claim coherence.
- **Multi-Vector Corroboration Gate:** A single isolated visual anomaly (e.g. one stock photo or compression artifact) **cannot unilaterally trigger HIGH risk**. Escalation strictly requires $\ge 2$ independent corroborated severe signals.
- **5-Tier Actionable Classification Model:** Replaces rigid reject/pass binaries with operational risk tiers (**CLEAR**, **LOW**, **MEDIUM**, **ELEVATED**, **HIGH — MANUAL REVIEW**). **Strictly no auto-rejections** — high-risk cases are routed to senior underwriters with an explainable audit trail.

### ⚡ Performance Optimization & Real-Time WebSockets
- **In-Memory Perceptual LRU Cache:** Sub-millisecond vector retrieval for repeated and duplicate image comparisons.
- **Real-Time WebSockets:** Live stage events and streaming progress percentage (`/ws/jobs/{job_id}`).

---

## 3. System Architecture

```text
visual-consistency-engine/
├── backend/
│   ├── main.py                     # FastAPI application entry point & CORS configuration
│   ├── api/
│   │   ├── routes.py               # Async merchant analysis REST routes (/api/analyse-merchant, jobs)
│   │   ├── job_manager.py          # Background worker queue & job lifecycle state machine
│   │   └── websockets.py           # Real-time WebSocket broadcasting (/ws/jobs/{job_id})
│   ├── routes/
│   │   └── analyze.py              # Synchronous analysis & multipart upload pipeline
│   ├── visual/
│   │   ├── vit_embeddings.py       # ViT-Base loader, LRU cache & cosine similarity
│   │   ├── image_reuse.py          # Multi-image catalog reuse & top-k similarity
│   │   ├── logo_check.py           # Brand logo consistency against verified databases
│   │   ├── manipulation.py         # Error Level Analysis (ELA) & Laplacian gradient forensics
│   │   └── heatmap.py              # Explainable heatmap colormapping & bounding box extraction
│   ├── crawler/
│   │   ├── site_crawler.py         # Resilient website crawler & metadata parser
│   │   ├── image_extractor.py      # Image filtering, priority scoring & dHash deduplication
│   │   └── ssrf_validator.py       # Strict IP / DNS / subnet security validator
│   ├── online_evidence/
│   │   ├── candidate_search.py     # Reverse visual search & candidate discovery
│   │   ├── verifier.py             # ViT verification, 4-status matching & domain attribution
│   │   ├── reasoning.py            # Evidence synthesis & explainable rationale generation
│   │   └── provider.py             # Serper.dev Google Search & DuckDuckGo fallback provider
│   ├── scoring/
│   │   ├── visual_score.py         # Sub-score aggregation (E1/E4 separation, logo, manipulation)
│   │   └── fusion.py               # 5-tier multimodal fusion & corroboration gates
│   ├── services/
│   │   ├── evidence_fusion.py      # Unified end-to-end evidence fusion & live ViT index
│   │   ├── evidence_normalizer.py  # Soft-trust, stock & supplier domain classification
│   │   └── visual_risk_scorer.py   # High-level visual risk scoring
│   ├── dataset/                    # Reference catalog images, brand logos & eval benchmarks
│   └── tests/                      # Comprehensive 34-test hermetic unit & calibration suite
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main application dashboard & state orchestration
│   │   ├── index.css               # Premium design system (dark mode, glassmorphism, animations)
│   │   ├── components/
│   │   │   ├── Header.jsx          # App header & status indicator
│   │   │   ├── MerchantForm.jsx    # URL submission, archetype presets & live progress bar
│   │   │   ├── RiskCards.jsx       # 5-tier scorecards & gauge breakdown
│   │   │   ├── HeatmapViewer.jsx   # Interactive forensic tampering inspector & threshold toggle
│   │   │   ├── EvidenceGrid.jsx    # Candidate comparison grid & source attribution
│   │   │   ├── ClaimVsEvidence.jsx # Text claim vs visual evidence reconciliation matrix
│   │   │   └── EvidenceFusionCards.jsx # Detailed forensic sub-scores
│   │   └── api/                    # REST client & WebSocket manager
│   ├── package.json                # Frontend dependencies
│   └── vite.config.js              # Vite server & proxy configuration
├── dataset/                        # Demo assets & interactive test scenarios
├── generate_demo_dataset.py        # Demo dataset & synthetic evaluation generator
├── demo_real_crawl.py              # Real-world web crawl demo script (public storefronts)
├── test_pipeline.py                # 15-module end-to-end integration test suite
├── requirements.txt                # Python backend dependencies
└── README.md                       # Complete documentation
```

---

## 4. Project Structure & Key Files

| File / Directory | Purpose |
|---|---|
| [`backend/main.py`](file:///d:/razorpay/backend/main.py) | Application entry point; initializes ViT weights and mounts REST and WebSocket routers. |
| [`backend/scoring/fusion.py`](file:///d:/razorpay/backend/scoring/fusion.py) | 5-Tier multimodal risk fusion, multi-signal corroboration gates, and human-readable explanations. |
| [`backend/scoring/visual_score.py`](file:///d:/razorpay/backend/scoring/visual_score.py) | E1/E4 signal separation, sub-score weighting, and visual risk calculation. |
| [`backend/online_evidence/verifier.py`](file:///d:/razorpay/backend/online_evidence/verifier.py) | Candidate verification with 4-status taxonomy (`NO_EXTERNAL_MATCH`, `WEAK_MATCH`, `INSUFFICIENT_EVIDENCE`, `CORROBORATED_EXTERNAL_MATCH`). |
| [`backend/services/evidence_normalizer.py`](file:///d:/razorpay/backend/services/evidence_normalizer.py) | Domain categorization (marketplaces, stock sites, supplier catalogs, image aggregators). |
| [`backend/visual/vit_embeddings.py`](file:///d:/razorpay/backend/visual/vit_embeddings.py) | ViT-Base embedding generation with in-memory perceptual LRU cache. |
| [`backend/visual/manipulation.py`](file:///d:/razorpay/backend/visual/manipulation.py) | Forensic algorithms (ELA compression residual + high-frequency noise). |
| [`frontend/src/components/MerchantForm.jsx`](file:///d:/razorpay/frontend/src/components/MerchantForm.jsx) | Interactive archetype preset chips and live streaming progress bar. |
| [`backend/tests/test_automated_engine.py`](file:///d:/razorpay/backend/tests/test_automated_engine.py) | Comprehensive 34-test calibration and hermetic safety verification suite. |

---

## 5. Installation & Quickstart Guide

### Prerequisites
- **Python:** 3.10 or higher
- **Node.js:** 18.x or higher
- **Package Manager:** `pip` and `npm`
- **Hardware:** Works on CPU (standard x86_64 / ARM64); GPU (CUDA) utilized automatically if available.

---

### Step 1: Clone and Set Up Backend

```bash
# Clone repository
git clone https://github.com/mohanraj-1810/Visual-Consistency-Evidence-Engine-Razorpay.git
cd Visual-Consistency-Evidence-Engine-Razorpay

# Create and activate Python virtual environment
# macOS / Linux:
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 2: Set Up Frontend

```bash
# In a new terminal, navigate to the frontend directory
cd frontend
npm install
cd ..
```

---

### Step 3: Launch Backend & Frontend

#### Terminal 1: Backend Server (FastAPI)
```bash
python backend/main.py --host 0.0.0.0 --port 8000
```
- **API URL:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

#### Terminal 2: Frontend Development Server (React + Vite)
```bash
cd frontend
npm run dev
```
- **Web Cockpit:** `http://localhost:5173`

---

## 6. Interactive Frontend & Analyst Cockpit

1. **Archetype Presets:** Test common underwriting scenarios with one click:
   - 🟢 **Standard Storefront (Clean):** Baseline legitimate e-commerce storefront.
   - 🟣 **Anti-Bot Protected (WAF 403):** Cloudflare / Bot-protected domain.
   - 🟡 **Redirect Loop (Safety Limit):** Catches cyclic and deep redirects.
   - 🔵 **Fintech Platform (Razorpay):** Infrastructure and brand asset validation.
   - ⚪ **Dead Domain (Unverifiable):** Unreachable / DNS failure handling.
2. **Streaming Progress Bar:** Live percentage tracker bound to WebSocket events.
3. **5-Tier Color Badges:** Visual risk indicator cards calibrated from CLEAR (`#16a34a`) to HIGH (`#dc2626`).
4. **Interactive Forensic Heatmap Viewer:** Sliders for ELA compression opacity and bounding box inspections.
5. **Claim vs. Evidence Reconciliation Matrix:** Side-by-side verification of textual claims against empirical visual findings.

---

## 7. Operational Guidelines & 5-Tier Actionability Model

### 5-Tier Decision Support Framework

| Score Range | Tier | Status Label | Operational Action & Workflow |
|---|---|---|---|
| **0 – 29** | **CLEAR** | `CLEAR — AUTO-APPROVE` | **Auto-Approve:** Clean visual signals; normal real-time transaction monitoring. |
| **30 – 49** | **LOW** | `LOW — STANDARD ONBOARDING` | **Standard Flow:** Standard statutory KYC validation. |
| **50 – 64** | **MEDIUM** | `MEDIUM — ENHANCED VERIFICATION` | **Automated Document Request:** Request supplier invoices or distributor authorization. |
| **65 – 79** | **ELEVATED** | `ELEVATED — CONDITIONAL APPROVAL` | **Conditional Approval:** Enable 90-day enhanced risk monitoring and invoice audit. |
| **80 – 100** | **HIGH** | `HIGH — MANUAL REVIEW` | **Manual Review Escalation:** Route to Senior Risk Operations (**Strictly never auto-reject**). |

### Corroboration & Risk Rules

1. **Single Anomaly Rule:** An isolated visual anomaly (single stock photo, Pinterest pin, compression artifact) is capped at **MEDIUM** to avoid false escalations.
2. **Multi-Signal Corroboration Rule:** Escalation to **HIGH** strictly requires $\ge 2$ independent corroborated severe signals (e.g. repeated stolen catalog photos + tampered invoice + altered logo).
3. **Supplier Catalog Rule:** Products matching known supplier platforms (Alibaba, IndiaMART, 1688) are recognized as wholesale sourcing and capped at **LOW/MEDIUM**.
4. **Own-Brand Safeguard:** Merchants with original, unindexed imagery are assigned zero reuse risk penalty.

---

## 8. Evaluation & Automated Test Suites

### Running the Hermetic Calibration Suite (34 Tests)

```bash
# Run all unit, calibration, and safety test suites
python -m unittest discover backend/tests -v
```

**Calibration Test Suites Covered (`T1–T9`):**
- `[T1]` Single visual anomaly $\to$ Not HIGH (capped at Medium).
- `[T2]` Multiple strong matches $\to$ HIGH-eligible when corroborated.
- `[T3]` Generic marketplace imagery $\to$ Not HIGH.
- `[T4]` Strong external match without corroboration $\to$ `INSUFFICIENT_EVIDENCE`.
- `[T5]` Repeated corroborating matches $\to$ `CORROBORATED_EXTERNAL_MATCH`.
- `[T6]` Unique own-brand catalog $\to$ Zero penalty (`e4_score = 0`).
- `[T7]` Legitimate marketing storefronts $\to$ Low/Medium tier.
- `[T8]` Coordinated multi-vector fraud $\to$ High risk with manual review.
- `[T9]` Soft-trust single matches (Pinterest/Aggregators) $\to$ Low score cap.
- `[Safety]` SSRF protection, loopback blocking, WebSocket streaming, and zero-auto-rejection compliance.

### Running End-to-End Integration Suite

```bash
python test_pipeline.py
```

---

## 9. Limitations & Future Roadmap

- **Cold-Start Brand Coverage:** Newly incorporated brands without a digital footprint rely on platform-wide reference catalog deduplication.
- **Static Image Analysis:** Storefronts utilizing video-only listings are parsed via static thumbnail frames.
- **Roadmap:**
  - [x] Pretrained ViT embeddings, LRU embedding cache, ELA forensics, SSRF crawler.
  - [x] 5-Tier operational actionability model, corroboration gates, and soft-trust normalization.
  - [ ] Video frame extraction for short-form product reels.
  - [ ] Cross-merchant graph clustering for distributed image-sharing syndicates.

---

## 👥 License

This project is licensed under the [MIT License](LICENSE).

