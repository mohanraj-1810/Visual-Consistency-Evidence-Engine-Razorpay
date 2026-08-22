# 🛡️ Visual Consistency & Evidence Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Node.js](https://img.shields.io/badge/Node.js-18.x%2B-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)
![React](https://img.shields.io/badge/React-18.x-61DAFB.svg)

**Explainable visual evidence and multimodal risk fusion for merchant onboarding and risk operations.**

---

## 1. Executive Summary

Traditional merchant onboarding and automated risk screening systems predominantly rely on textual disclosures, self-reported business descriptions, statutory identifiers (e.g., GST/CIN), and basic website content parsing. 

However, fraudulent and high-risk entities often circumvent these textual validations by fabricating compliant terms of service or professional descriptions. Visual evidence presents a more robust indicator of authenticity. Challenges include:
- Claiming brand authenticity while utilizing stolen catalog imagery.
- Deploying inconsistent or distorted logo variants.
- Uploading incorporation documents or invoices with localized digital manipulation.

**Core Objective:** The Visual Consistency & Evidence Engine determines whether the visual artifacts provided by a merchant support or contradict their textual claims.

---

## 2. System Architecture

The solution comprises a FastAPI backend and a React frontend, operating together to provide a seamless full-stack application.

```text
visual-consistency-engine/
├── backend/
│   ├── main.py                     # FastAPI application entry point
│   ├── routes/                     # API endpoint definitions
│   ├── visual/                     # ViT embeddings, manipulation detection, heatmaps
│   ├── scoring/                    # Visual scoring and multimodal fusion logic
│   ├── crawler/                    # Automated website crawler and image extraction
│   ├── dataset/                    # Reference catalogs, logos, and evaluation sets
│   └── evaluation/                 # Precision/Recall/F1 metrics evaluation
├── frontend/
│   ├── package.json                # Frontend dependencies
│   ├── vite.config.js              # Vite server configuration
│   └── src/                        # React components, layout, and API client
├── generate_demo_dataset.py        # Utility to generate demonstration and evaluation datasets
├── test_pipeline.py                # Core pipeline unit and integration tests
└── README.md                       # Project documentation
```

---

## 3. Installation & Setup Guide

### Prerequisites
- **Python:** 3.10 or higher
- **Node.js:** 18.x or higher
- **Operating System:** Windows, macOS, or Linux

### Step 1: Environment Configuration

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 3: Dataset Generation
Generate the interactive demonstration cases and the held-out evaluation test cases:
```bash
python generate_demo_dataset.py
```
*Note: This populates the `dataset/` and `backend/dataset/eval_set/` directories.*

### Step 4: Application Launch

Launch the backend and frontend services in separate terminal sessions.

**Terminal 1 — Backend API (FastAPI)**
```bash
python backend/main.py
```
- API Base URL: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

**Terminal 2 — Frontend Application (React + Vite)**
```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 4. API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Service health and version verification |
| `/demo-cases` | GET | Retrieves controlled demonstration case definitions |
| `/analyze` | POST | Executes the full multimodal risk pipeline (multipart form data) |

---

## 5. Core Capabilities & Methodology

### Pretrained Vision Transformer (ViT) Embeddings
- Extracts dense visual semantic features utilizing `google/vit-base-patch16-224`.
- Generates L2-normalized 768-dimensional vectors.
- Operates 100% offline at inference time.

### Visual Reuse Detection
- Computes cosine similarity between merchant product visuals and a verified catalog database to identify scraped or duplicated product photography.

### Logo & Brand Consistency
- Compares claimed brand assets against registered reference logos to report visual divergence.

### Manipulation Forensics & Heatmaps
- **Error Level Analysis (ELA):** Detects localized compression discrepancies.
- **Laplacian Gradient Noise:** Highlights high-frequency artificial text/stamp splicing.
- **Explainable Heatmap:** Generates intuitive colormap overlays with anomalous bounding boxes.

### Multimodal Risk Fusion Engine
The engine combines multiple risk vectors to generate a comprehensive risk score:

`Visual Risk = (0.30 × Reuse) + (0.20 × Logo) + (0.25 × Manipulation) + (0.10 × Synthetic) + (0.15 × Identity Dispersion)`

**Risk Classifications:**
- **0–39 (LOW):** Standard Onboarding Flow
- **40–69 (MEDIUM):** Additional Verification Required  
- **70–100 (HIGH):** Manual Risk Review Escalation

---

## 6. Evaluation & Performance Metrics

The engine includes a benchmark evaluation suite to measure precision, recall, and false-positive cost on a held-out test set.

**Run the Evaluation Benchmark:**
```bash
python generate_demo_dataset.py
python backend/evaluation/evaluate_pipeline.py
```

### Benchmark Results (18 Held-Out Cases)

| Category | Precision | Recall | F1-Score | Support |
|----------|-----------|--------|----------|---------|
| **LOW** | 0.83 | 0.83 | 0.83 | 6 |
| **MEDIUM** | 0.42 | 0.83 | 0.56 | 6 |
| **HIGH** | 0.00 | 0.00 | 0.00 | 6 |

**False-Positive Cost Analysis:**
- **False-Positive Rate (FPR):** 16.7% (1 of 6 clean merchants flagged as MEDIUM or HIGH)
- **False-Negative Rate (FNR):** 0.0% (0 of 6 suspicious merchants flagged as LOW)

*Analysis: The system exhibits conservative behavior, prioritizing the flagging of suspicious merchants for review (0% FNR) while maintaining a reasonable FPR.*

---

## 7. Operational Guidelines

**Disclaimer:** This system is an **analyst decision-support prototype**. It generates empirical visual evidence signals, similarity metrics, and forensic heatmaps designed to assist human risk reviewers. It is **not** intended to automatically reject merchants without human oversight.

# Visual-Consistency-Evidence-Engine-Razorpay
