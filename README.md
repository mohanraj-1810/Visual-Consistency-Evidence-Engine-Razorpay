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

### 🛡️ Online Evidence Retrieval & Zero Penalty Safeguard
- Discovers external visual matches across e-commerce marketplaces and reference repositories.
- **Zero Penalty Protection for Original/Artisanal Brands:** Prevents penalizing unique, proprietary photography that has no external matches.
- Multi-tier matching thresholds: *Identical Reuse (≥0.92)*, *High Similarity (0.80–0.91)*, *Moderate (0.65–0.79)*, *Independent/Original (<0.65)*.

### ⚖️ Multimodal Risk Fusion Engine
- Combines visual reuse, logo divergence, forensic tampering, and text-visual claim coherence.
- Generates transparent, human-readable risk breakdowns with clear analyst rationale.
- Actionable risk classifications: **LOW (0–39)**, **MEDIUM (40–69)**, **HIGH (70–100)**.

### ⚡ Asynchronous Job Queue & Real-Time WebSockets
- Non-blocking background execution via `JobManager`.
- Real-time progress updates streamed directly to frontend clients via WebSockets (`/ws/jobs/{job_id}`).

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
│   │   ├── vit_embeddings.py       # Vision Transformer (ViT-Base) model loader & cosine similarity
│   │   ├── image_reuse.py          # Catalog reuse & cross-image identity coherence
│   │   ├── logo_check.py           # Brand logo consistency against verified databases
│   │   ├── manipulation.py         # Error Level Analysis (ELA) & Laplacian gradient forensics
│   │   └── heatmap.py              # Explainable heatmap colormapping & bounding box extraction
│   ├── crawler/
│   │   ├── site_crawler.py         # Resilient website crawler & metadata parser
│   │   ├── image_extractor.py      # Image filtering, priority scoring & dHash deduplication
│   │   └── ssrf_validator.py       # Strict IP / DNS / subnet security validator
│   ├── online_evidence/
│   │   ├── candidate_search.py     # Reverse visual search & candidate discovery
│   │   ├── verifier.py             # ViT verification, similarity thresholding & domain attribution
│   │   ├── reasoning.py            # Evidence synthesis & explainable rationale generation
│   │   └── provider.py             # Serper.dev Google Search & DuckDuckGo fallback provider
│   ├── scoring/
│   │   ├── visual_score.py         # Sub-score aggregation (reuse, logo, manipulation, synthetic)
│   │   └── fusion.py               # Multimodal fusion & text vs visual discrepancy logic
│   ├── services/
│   │   ├── evidence_fusion.py      # Unified end-to-end evidence fusion service
│   │   ├── evidence_normalizer.py  # Data contract formatting & sanitization
│   │   └── visual_risk_scorer.py   # High-level risk score calculator
│   ├── dataset/                    # Reference catalog images, brand logos & eval benchmarks
│   └── evaluation/                 # Metrics suite (Precision, Recall, F1, Latency benchmarks)
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main application dashboard & state orchestration
│   │   ├── index.css               # Premium design system (dark mode, glassmorphism, animations)
│   │   ├── components/
│   │   │   ├── Header.jsx          # App header & status indicator
│   │   │   ├── MerchantForm.jsx    # URL submission & interactive demo selector
│   │   │   ├── RiskCards.jsx       # Multimodal scorecards & risk gauge breakdown
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
| [`backend/api/job_manager.py`](file:///d:/razorpay/backend/api/job_manager.py) | Manages asynchronous crawling and analysis jobs across thread pools. |
| [`backend/visual/vit_embeddings.py`](file:///d:/razorpay/backend/visual/vit_embeddings.py) | HuggingFace `google/vit-base-patch16-224` inference and feature extraction. |
| [`backend/visual/manipulation.py`](file:///d:/razorpay/backend/visual/manipulation.py) | Forensic algorithms (ELA compression residual + high-frequency noise). |
| [`backend/scoring/fusion.py`](file:///d:/razorpay/backend/scoring/fusion.py) | Multimodal fusion balancing visual risk, textual claims, and domain mismatch. |
| [`frontend/src/App.jsx`](file:///d:/razorpay/frontend/src/App.jsx) | React single-page application connecting to backend REST and WebSocket APIs. |
| [`test_pipeline.py`](file:///d:/razorpay/test_pipeline.py) | Comprehensive 15-module test runner covering all engine components. |
| [`demo_real_crawl.py`](file:///d:/razorpay/demo_real_crawl.py) | Real-world demo crawler showcasing live ingestion and ViT analysis on real sites. |

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

### Step 3: Generate Demonstration & Evaluation Datasets

```bash
# Generates synthetic evaluation benchmarks and demo scenario assets
python generate_demo_dataset.py
```

*This command populates `dataset/` and `backend/dataset/eval_set/` with clean reference images, manipulated test samples, and cross-category demonstration fixtures.*

---

### Step 4: Launch the Full-Stack Application

Start the backend and frontend in separate terminal windows:

#### Terminal 1: Backend Server (FastAPI)
```bash
python backend/main.py --host 0.0.0.0 --port 8000
```
- **API URL:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`

#### Terminal 2: Frontend Development Server (React + Vite)
```bash
cd frontend
npm run dev
```
- **Web Cockpit:** `http://localhost:5173`

---

## 6. Interactive Frontend & Analyst Cockpit

The React frontend provides a glassmorphic risk intelligence interface designed specifically for risk reviewers:

1. **Preset Demo Scenarios:** Select one-click pre-configured merchant cases:
   - 🟢 **Clean Artisan Merchant (LOW Risk):** Original handcrafted goods, authentic logo, clean forensics.
   - 🟡 **Questionable Dropshipper (MEDIUM Risk):** Stock catalog mix, minor dispersion, unregistered brand.
   - 🔴 **Counterfeit Luxury Storefront (HIGH Risk):** 98% visual similarity to registered trademarked catalogs, manipulated invoices, altered logo.
2. **Live URL Crawler:** Enter any public merchant URL to trigger the crawler, image prioritization, and reverse visual verification.
3. **Interactive Forensic Heatmap Viewer:**
   - Slide forensic opacity to inspect localized compression discrepancies.
   - Toggle bounding box overlays around spliced text and altered seals.
4. **Claim vs. Evidence Matrix:**
   - Visual side-by-side comparison between merchant-declared business type and empirical visual findings.
5. **Evidence Grid:**
   - Displays matched candidate images from the web or reference catalog with source URLs, similarity percentages, and match categories.

---

## 7. API Reference & WebSocket Specs

### Synchronous REST Endpoints

#### `GET /health`
Verifies backend service availability and pre-warmed model status.

#### `GET /demo-cases`
Returns a list of pre-configured demo cases for UI testing.

#### `POST /analyze`
Accepts multipart form data with images and metadata for immediate, synchronous analysis.

---

### Asynchronous REST Endpoints (Web Crawler Pipeline)

#### `POST /api/analyse-merchant`
Submits a merchant website URL for asynchronous crawling, ViT embedding, and forensic analysis.

**Request Body:**
```json
{
  "merchant_id": "merchant_tech_001",
  "website_url": "https://example-electronics-store.com",
  "claimed_brand": "Apex Audio",
  "merchant_category": "electronics"
}
```

**Response (`202 Accepted`):**
```json
{
  "job_id": "job_a1b2c3d4e5f6",
  "status": "QUEUED"
}
```

#### `GET /api/analysis-jobs/{job_id}`
Polls the execution state of an ongoing job.

**Status Pipeline:** `QUEUED` ➔ `CRAWLING` ➔ `EXTRACTING_IMAGES` ➔ `SEARCHING_WEB` ➔ `ANALYSING_FORENSICS` ➔ `SCORING` ➔ `COMPLETED` | `FAILED`

#### `GET /api/analysis-jobs/{job_id}/report`
Retrieves the complete visual risk report once the job status reaches `COMPLETED`.

---

### Real-Time WebSocket Streaming

#### `WS /ws/jobs/{job_id}`
Clients connect to receive live JSON events as the pipeline progresses:
```json
{
  "job_id": "job_a1b2c3d4e5f6",
  "stage": "SEARCHING_WEB",
  "progress_pct": 55,
  "message": "Comparing 4 catalog images against reference databases..."
}
```

---

## 8. Evaluation, Testing & Benchmarking

### Running the End-to-End Test Suite

The repository includes a 15-module verification suite covering all components:

```bash
# Run all 15 verification modules
python test_pipeline.py

# Run with verbose logs
python test_pipeline.py --verbose
```

**Test Coverage:**
- `[1]` Pretrained Vision Transformer (ViT) Backbone
- `[2]` Image Reuse & Stolen Catalog Detection
- `[3]` Brand Logo Consistency Engine
- `[4]` ELA Tampering Forensics & Heatmap Generation
- `[5]` Cross-Image Visual Identity Coherence
- `[6]` Multimodal Risk Fusion & Escalation
- `[7]` Website Crawling & Metadata Extraction
- `[8]` Image Filtering (UI / Pixel / Icon Elimination)
- `[9]` Image Deduplication & Perceptual Grouping
- `[10]` Online Evidence Search & Candidate Retrieval
- `[11]` ViT Visual Verification & Similarity Calculation
- `[12]` Evidence Ranking & Strength Classification
- `[13]` Own-Brand / No-Match Handling (Zero Penalty Protection)
- `[14]` Strong External-Match Case Handling (Risk Escalation)
- `[15]` End-to-End Website Analysis Pipeline

---

### Running the Quantitative Evaluation Benchmark

```bash
python generate_demo_dataset.py
python backend/evaluation/evaluate_pipeline.py
```

*Results are written to `backend/evaluation/results.json`.*

#### Evaluation Metrics Summary (n=18 held-out test cases)

> ℹ️ **Scope Note:** Benchmarked on a held-out synthetic evaluation set across varied merchant categories.

| Risk Category | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **LOW** | 0.83 | 0.83 | 0.83 | 6 |
| **MEDIUM** | 0.83 | 0.83 | 0.83 | 6 |
| **HIGH** | 1.00 | 1.00 | 1.00 | 6 |

- **Overall Accuracy:** 88.9% (16/18 correct)
- **Macro F1:** 0.889
- **Weighted F1:** 0.889
- **High-Risk Recall:** 100% (No fraudulent merchant misclassified as low risk)
- **Mean Processing Latency:** ~2.1 seconds per merchant (CPU-only benchmark)

---

### Live Real-World Crawling Demonstration

To demonstrate the crawler and ViT pipeline operating on live, public websites:

```bash
# Runs the live crawler against public test e-commerce storefronts
python demo_real_crawl.py

# Or crawl custom target URLs:
python demo_real_crawl.py --urls "https://books.toscrape.com/" "https://webscraper.io/test-sites/e-commerce/allinone"
```

*Outputs are saved to `results/real_crawl_demo.json`.*

---

## 9. Operational Guidelines & Risk Scoring Model

### Risk Scoring Formula

The aggregate visual risk score $S_{\text{visual}} \in [0, 100]$ is computed as:

$$S_{\text{visual}} = 0.30 \cdot S_{\text{reuse}} + 0.20 \cdot S_{\text{logo}} + 0.25 \cdot S_{\text{forensics}} + 0.10 \cdot S_{\text{synthetic}} + 0.15 \cdot S_{\text{dispersion}}$$

Where:
- $S_{\text{reuse}}$: Maximum cosine similarity against external unowned catalogs.
- $S_{\text{logo}}$: Visual divergence between claimed brand logo and verified registry.
- $S_{\text{forensics}}$: ELA compression anomalies and high-frequency edge splicing metrics.
- $S_{\text{synthetic}}$: Synthetic / AI-generated artifact likelihood.
- $S_{\text{dispersion}}$: Inconsistency in aesthetic quality across the merchant's catalog.

### Decision-Support Tiers

| Score Range | Tier | Operational Action |
|---|---|---|
| **0 – 39** | **LOW** | **Standard Onboarding:** Low visual risk; standard automated onboarding flow. |
| **40 – 69** | **MEDIUM** | **Secondary Verification:** Request original high-res product photos or supplier invoices. |
| **70 – 100** | **HIGH** | **Manual Review Escalation:** Flag for senior risk analyst; inspect heatmap and source attribution. |

---

## 10. Limitations & Future Roadmap

### Current Limitations
- **Cold-Start Brand Coverage:** Newly incorporated brands without a digital footprint rely on platform-wide reference catalog deduplication.
- **Static Image Analysis:** Storefronts utilizing video-only listings are parsed via static thumbnail frames.
- **Single Dominant Product Focus:** The primary pipeline evaluates top-ranked prioritized product visuals.

### Roadmap
- [x] **v1.0:** Pretrained ViT embeddings, ELA forensics, SSRF crawler, real-time WebSocket queue, and React dashboard.
- [ ] **v1.1:** Video frame extraction support for short-form product reels.
- [ ] **v2.0:** Cross-merchant graph clustering for detecting distributed image-sharing syndicates.
- [ ] **v2.1:** Direct automated integration with official trademark and patent registry APIs.

---

## 👥 Contributors & License

Developed for the **Razorpay Hackathon / Visual Risk Challenge**.

This project is licensed under the [MIT License](LICENSE).
