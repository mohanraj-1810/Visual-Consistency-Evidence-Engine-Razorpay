


# 📚 Visual Consistency & Evidence Engine — Documentation Hub

Welcome to the comprehensive documentation hub for the **Visual Consistency & Evidence Engine** (Razorpay Buildathon).

---

## 🧭 Documentation Navigator

| Document | Target Audience | Summary |
| :--- | :--- | :--- |
| [**System Overview (`/README.md`)**](file:///d:/razorpay/README.md) | All | Architectural deep-dive, system features, core tech stack, API overview & setup. |
| [**Docker Deployment (`/docs/DOCKER.md`)**](file:///d:/razorpay/docs/DOCKER.md) | DevOps & Evaluators | Single-command Docker Compose build, container ports, volume mounts, and troubleshooting. |
| [**Judge & Evaluator FAQ (`/docs/JUDGE_FAQ.md`)**](file:///d:/razorpay/docs/JUDGE_FAQ.md) | Technical Evaluators | Detailed answers regarding ViT embedding extraction, ELA manipulation analysis, SSRF crawler defenses, latency profiles, and corroboration gating. |
| [**Live Demo Script (`/docs/DEMO_SCRIPT.md`)**](file:///d:/razorpay/docs/DEMO_SCRIPT.md) | Presenters & Judges | Exact 3-minute evaluation pitch flow, merchant preset walk-throughs, and key talking points. |
| [**Buildathon Submission Spec (`/docs/BUILDATHON.md`)**](file:///d:/razorpay/docs/BUILDATHON.md) | Evaluators & Judges | Complete hackathon submission specs, metrics breakdown, problem statement fulfillment, and competitive moat. |
| [**Forensic Audit Report (`/backend/evaluation/HIGH_RISK_AUDIT.md`)**](file:///d:/razorpay/backend/evaluation/HIGH_RISK_AUDIT.md) | Risk & ML Engineers | Deep-dive case-by-case audit of the 23-merchant evaluation benchmark, corroboration analysis, and false-positive elimination. |

---

## 🏛️ System Architecture Quick View

```text
                                  ┌──────────────────────────────┐
                                  │   Merchant Website / Asset   │
                                  └──────────────┬───────────────┘
                                                 │
                                  ┌──────────────▼───────────────┐
                                  │  SSRF-Hardened Web Crawler   │
                                  │    (site_crawler.py)         │
                                  └──────────────┬───────────────┘
                                                 │
                                  ┌──────────────▼───────────────┐
                                  │ Asset Filtering & Priority   │
                                  │   (image_extractor.py)       │
                                  └──────────────┬───────────────┘
                                                 │
                                  ┌──────────────▼───────────────┐
                                  │  ViT Embedding Extraction    │
                                  │ (google/vit-base-patch16)    │
                                  └──────┬───────────────┬───────┘
                                         │               │
                 ┌───────────────────────┴──────┐ ┌──────┴───────────────────────┐
                 │  External Web Discovery      │ │   Local Platform ViT Index   │
                 │  (Serper.dev / DuckDuckGo)   │ │  (services/evidence_fusion)  │
                 └──────────────┬───────────────┘ └──────────────┬───────────────┘
                                │                                │
                 ┌──────────────▼───────────────┐ ┌──────────────▼───────────────┐
                 │   Logo Consistency Engine    │ │   Forensic ELA & Tampering   │
                 │     (logo_check.py)          │ │    (manipulation.py)         │
                 └──────────────┬───────────────┘ └──────────────┬───────────────┘
                                │                                │
                                └───────────────┬────────────────┘
                                                │
                                  ┌─────────────▼──────────────┐
                                  │ Multimodal Risk Fusion     │
                                  │ with Corroboration Gating  │
                                  │    (scoring/fusion.py)     │
                                  └─────────────┬──────────────┘
                                                │
                                  ┌─────────────▼──────────────┐
                                  │ 5-Tier Actionable Status   │
                                  │ & Explainable Audit Trail  │
                                  └─────────────┬──────────────┘
                                                │
                                  ┌─────────────▼──────────────┐
                                  │ Asynchronous Job Queue &   │
                                  │ Real-Time WebSockets       │
                                  │ (api/job_manager.py + WS)  │
                                  └─────────────┬──────────────┘
```

---

## ⚡ Quick Links & Commands

- **Run Locally (Docker):**
  ```bash
  docker compose up --build
  ```
- **Run Backend (Manual):**
  ```bash
  cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Run Frontend (Manual):**
  ```bash
  cd frontend && npm run dev
  ```
- **Run Evaluation Suite:**
  ```bash
  python -m backend.evaluation.evaluate_pipeline
  ```
