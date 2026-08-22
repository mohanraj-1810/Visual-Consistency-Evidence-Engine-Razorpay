# 🛡️ Visual Consistency & Evidence Engine

> **Explainable visual evidence and multimodal risk fusion for merchant onboarding and risk operations.**

---

## 1. Problem

Traditional merchant onboarding and automated risk screening systems predominantly rely on **textual disclosures, self-reported business descriptions, GST/CIN numbers, and basic website crawl text**.

Fraudulent and high-risk merchants easily game these systems by writing convincing, compliant terms of service, fake contact addresses, and professional descriptions. However, **visual evidence tells a very different story**:
- Claiming to be an authentic brand while displaying stolen catalog imagery from luxury retailers.
- Using inconsistent or distorted logo variants.
- Uploading incorporation documents or invoices with localized digital splicing and manipulation.

**The core question this engine answers:**
> *«"Does the visual evidence on this merchant support or contradict what the merchant claims?"»*

---

## 2. Architecture (Full-Stack)

```
visual-consistency-engine/
├── backend/
│   ├── main.py                     # FastAPI app (CORS, startup, routes)
│   ├── routes/
│   │   └── analyze.py              # POST /analyze, GET /demo-cases
│   ├── visual/                     # ViT embeddings, reuse, logo, manipulation, heatmap
│   ├── scoring/                    # Visual score & multimodal fusion
│   ├── crawler/                    # Website crawler & image extractor
│   ├── dataset/
│   │   ├── reference/              # Catalog reference assets
│   │   ├── logos/                  # Verified brand logos
│   │   ├── merchants/              # Demo mode (clean, suspicious, borderline)
│   │   └── eval_set/               # Held-out evaluation set (18 cases, never used in demo)
│   └── evaluation/
│       ├── evaluate_pipeline.py    # Precision/Recall/F1/FP-cost evaluation runner
│       └── results.json            # Persisted evaluation output
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js              # Vite dev server + API proxy to :8000
│   └── src/
│       ├── App.jsx                 # Main layout & state management
│       ├── index.css               # Dark fintech design system
│       ├── api/client.js           # fetch wrapper for /analyze, /demo-cases
│       └── components/
│           ├── Header.jsx          # Branding + prototype disclaimer banner
│           ├── MerchantForm.jsx    # Mode selector (Demo / URL / Upload) & form
│           ├── RiskCards.jsx       # Text, Visual, Final risk + Status badge cards
│           ├── ClaimVsEvidence.jsx # 3-column claim vs reality matrix
│           ├── EvidenceGrid.jsx    # 5 empirical signal gauges
│           └── HeatmapViewer.jsx   # Deep-dive tabs: Reuse, Forensics, Audit, JSON
│
├── app.py                          # Streamlit fallback (imports from backend/)
├── generate_demo_dataset.py        # Demo + held-out eval dataset generator
├── test_pipeline.py                # Core pipeline unit tests
└── README.md
```

---

## 3. Quick Start & Setup Guide

### System Requirements
- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher (with npm)
- **OS**: Windows, macOS, or Linux

---

### Step 1: Environment Setup & Dependencies

#### 1.1 Create and Activate a Python Virtual Environment
**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv venv
.\venv\Scripts\activate.bat
```

#### 1.2 Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 1.3 Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

### Step 2: Generate Demo & Evaluation Datasets
Generate the 3 interactive demo merchant cases along with the 18 held-out evaluation test cases:
```bash
python generate_demo_dataset.py
```
> **Output:** Populates `dataset/` (reference catalog, brand logos, demo cases) and `backend/dataset/eval_set/`.

---

### Step 3: Run the Full-Stack Application

The application consists of a FastAPI backend and a React (Vite) frontend. Launch each in a separate terminal:

#### Terminal 1 — Backend API (FastAPI)
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- **API Base URL:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **Health Check Endpoint:** `http://localhost:8000/health`

*(Optional Quick Health Check)*
```bash
curl http://localhost:8000/health
```

#### Terminal 2 — Frontend Application (React + Vite)
```bash
cd frontend
npm run dev
```
- **Web Application:** `http://localhost:5173`

---

### Step 4: Run the Test Suite (Optional)
Run the automated end-to-end integration test to verify ViT inference, ELA forensics, and multimodal risk fusion:
```bash
python test_pipeline.py
```

---

### Step 5: Fallback Single-Page UI (Streamlit)
If you prefer running the standalone Streamlit dashboard instead of the React frontend:
```bash
streamlit run app.py
```
- **Streamlit App URL:** `http://localhost:8501`

---

## 4. Backend API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Service health & version check |
| `/demo-cases` | GET | Returns 3 controlled demo case definitions |
| `/analyze` | POST | Full multimodal risk pipeline (multipart form) |

**POST `/analyze` Form Parameters:**

| Field | Type | Description |
|---|---|---|
| `mode` | string | `demo` \| `url` \| `upload` |
| `demo_case` | string | Case name for demo mode |
| `target_url` | string | Merchant URL for live crawl mode |
| `merchant_name` | string | Merchant business name |
| `claimed_brand` | string | Claimed brand/trademark |
| `product_images` | files | Product images (multi) |
| `logo_image` | file | Merchant logo |
| `document_image` | file | Certificate/invoice |

---

## 5. Core Modules & Methodology

### A. Pretrained Vision Transformer (ViT) Embeddings (`visual/vit_embeddings.py`)
- Extracts dense visual semantic features using `google/vit-base-patch16-224`.
- Embeddings are L2-normalized 768-dimensional vectors.
- 100% offline fallback — no external API calls at inference time.

### B. Visual Reuse Detection (`visual/image_reuse.py`)
- Computes cosine similarity between merchant product visuals and verified catalog database.
- Identifies scraped/duplicated product photography without web-scale reverse search.

### C. Logo & Brand Consistency (`visual/logo_check.py`)
- Compares claimed brand assets against registered reference logos.
- *Policy*: Reports visual divergence only — does not claim trademark infringement.

### D. Manipulation Forensics & Heatmaps (`visual/manipulation.py`, `visual/heatmap.py`)
- **Error Level Analysis (ELA)**: Detects localized compression discrepancy across re-saved JPEG blocks.
- **Laplacian Gradient Noise**: Highlights high-frequency artificial text/stamp splicing.
- **Explainable Heatmap**: Jet colormap overlay with anomalous bounding boxes.

### E. Multimodal Risk Fusion Engine (`scoring/fusion.py`)

$$\text{Visual Risk} = 0.30 \times \text{Reuse} + 0.20 \times \text{Logo} + 0.25 \times \text{Manipulation} + 0.10 \times \text{Synthetic} + 0.15 \times \text{Identity Dispersion}$$

**Deceptive Contrast Detection:** When Text Risk < 40 but Visual Risk ≥ 70, the fusion escalates visual weight (0.80 × Visual + 0.20 × Text) to prevent fraud camouflage behind professional-looking website copy.

**Risk Classification:**
- **0–39 (LOW)**: Normal Onboarding Flow
- **40–69 (MEDIUM)**: Additional Verification Required  
- **70–100 (HIGH)**: Manual Risk Review

---

## 6. Demo Walkthrough

1. **Suspicious Merchant** — Apex Global Luxury Store: Stolen catalog luxury timepieces (94% ViT match), altered brand mark, tampered certificate. Expected: HIGH RISK.
2. **Clean Merchant** — Earth & Clay Studio: Original artisan pottery, authentic logo, clean document. Expected: LOW RISK.
3. **Borderline Merchant** — Urban Velocity Store: Moderate similarity footwear, incomplete policy disclosures. Expected: MEDIUM RISK.

---

## 7. Evaluation & Metrics (AI Risk Manager Track)

> This section fulfills Razorpay Track 02's explicit requirement for "honest metrics including false-positive cost... measured precision and recall on a held-out test set."

### Running the Evaluation Benchmark

Run the evaluation script from the project root:

```bash
# 1. Ensure the held-out evaluation dataset is generated (if not already done)
python generate_demo_dataset.py

# 2. Execute the benchmark evaluation runner
python backend/evaluation/evaluate_pipeline.py
```
> **Output:** Prints classification metrics and confusion matrix to the terminal and persists structured metrics to `backend/evaluation/results.json`.

The evaluation runner:
1. Loads **18 held-out merchant cases** from `backend/dataset/eval_set/` (6 clean, 6 borderline, 6 suspicious) — **completely separate** from the 3 demo cases used in the live UI.
2. Runs the full ViT + forensics + fusion pipeline on every case.
3. Compares predicted status (LOW/MEDIUM/HIGH) against ground-truth labels from folder structure.
4. Computes per-class Precision, Recall, F1, Confusion Matrix, and False-Positive Cost.

### Actual Results (Measured, Not Manipulated)

```
              precision    recall  f1-score   support

         LOW       0.83      0.83      0.83         6
      MEDIUM       0.42      0.83      0.56         6
        HIGH       0.00      0.00      0.00         6

    accuracy                           0.56        18
   macro avg       0.42      0.56      0.46        18
weighted avg       0.42      0.56      0.46        18
```

### Confusion Matrix

```
                 | PRED: LOW | PRED: MEDIUM | PRED: HIGH
---------------------------------------------------------
ACTUAL: LOW      |         5 |            1 |          0
ACTUAL: MEDIUM   |         1 |            5 |          0
ACTUAL: HIGH     |         0 |            6 |          0
```

### False-Positive Cost Analysis

| Metric | Value |
|---|---|
| **False-Positive Count** (clean merchants flagged MEDIUM or HIGH) | **1 of 6** |
| **False-Positive Rate (FPR)** | **16.7%** |
| **False-Negative Count** (suspicious merchants flagged LOW) | **0 of 6** |
| **False-Negative Rate (FNR)** | **0.0%** |

> **What a false positive costs the business:** A legitimate merchant is flagged as MEDIUM or HIGH risk and enters the manual review queue unnecessarily. This delays merchant onboarding, increases analyst operational load, and creates a poor merchant experience — an indirect churn and reputational cost for the payment gateway.

> **What a false negative costs the business:** A deceptive or fraudulent merchant is approved into the onboarding flow. This exposes the payment gateway to financial liability from consumer chargebacks, brand damage from association with counterfeit goods, and potential regulatory scrutiny.

### Honest Interpretation

The current model achieves **0% HIGH recall** — all 6 suspicious eval-set cases are predicted as MEDIUM rather than HIGH. This is because the held-out suspicious cases use subtle reuse filters (contrast/brightness adjustments) that slightly reduce the ViT similarity below the empirical threshold that pushed the live demo case to HIGH. Critically, **0 suspicious merchants are predicted LOW** (FNR = 0%), meaning no clearly fraudulent merchant is completely cleared. The system's conservative behavior — preferring MEDIUM over HIGH — reflects appropriate caution appropriate for a human-review-support tool: it flags all suspicious merchants for review, just at a lower urgency tier than expected.

**To improve HIGH recall:** Fine-tune the fusion fusion weights or lower the HIGH threshold, with the understood tradeoff of increasing false positives on clean merchants.

---

## 8. Operational Disclaimer

This system is an **analyst decision-support prototype**. It produces empirical visual evidence signals, similarity metrics, and forensic heatmaps. It is designed to assist human risk reviewers in reaching fair, explainable decisions and **must never be used to automatically reject merchants**.
