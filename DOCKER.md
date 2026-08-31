# 🐳 Docker Deployment Guide — Visual Consistency & Evidence Engine

This guide explains how to run, test, and manage the **Visual Consistency & Evidence Engine** using Docker and Docker Compose.

---

## 1. Requirements

- **Docker Desktop** (version 24.0+ recommended) or **Docker Engine & Docker Compose v2+**
- **WSL 2 backend** enabled (on Windows)
- Minimum System Resources:
  - 4 GB RAM available to Docker
  - 2 CPU cores
  - No GPU or CUDA required (runs 100% on CPU)

---

## 2. Quick Start

Run the entire application (Backend API + React Frontend Cockpit + ViT Model Backbone) in a single command:

```bash
# 1. (Optional) Set up your environment file
cp .env.example .env

# 2. Build and start the container
docker compose up --build
```

To run in detached background mode:
```bash
docker compose up --build -d
```

---

## 3. Accessing the Application

Once started, the unified service is accessible at:

| Service / Interface | Local URL | Description |
| :--- | :--- | :--- |
| **React Analyst Cockpit** | [http://localhost:8000](http://localhost:8000) | Full visual risk dashboard with interactive presets & live crawling |
| **FastAPI Interactive Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI for exploring and executing REST & WebSocket endpoints |
| **Health Check Endpoint** | [http://localhost:8000/health](http://localhost:8000/health) | Readiness & provider configuration status |

---

## 4. Environment Variables

The application works completely out of the box without any external API keys (using built-in test fixtures and DuckDuckGo search fallback).

To enable live Google Images visual candidate queries with Serper:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Configure your Serper API key:
   ```env
   SERPER_API_KEY=your_actual_serper_api_key_here
   ```

*Note: `.env` is automatically ignored by `.gitignore` and `.dockerignore` to prevent accidental credential leakage.*

---

## 5. Model Cache & Persistence

The Vision Transformer backbone (`google/vit-base-patch16-224`) is pre-warmed on container startup.
- Downloaded model weights are saved in a persistent Docker volume (`visual_engine_hf_cache`).
- Subsequent restarts reuse the cached model weights instantly without re-downloading.

---

## 6. Stopping & Managing Containers

### Stop Containers
```bash
docker compose down
```

### View Live Logs
```bash
docker compose logs -f
```

### Inspect Container Health
```bash
docker compose ps
```

### Rebuild from Scratch (Clean Build)
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## 7. Running Tests & Evaluation Inside Docker

### Run the PyTest Suite (46 Tests)
```bash
docker compose exec visual-engine python -m pytest backend/tests/ -v
```

### Run Benchmark Evaluation (23 Cases Across 11 Archetypes)
```bash
docker compose exec visual-engine python backend/evaluation/evaluate_pipeline.py
```

---

## 8. Troubleshooting

### Port 8000 Already in Use
If port 8000 is occupied by another process on your machine, edit the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"
```
Then access the dashboard at `http://localhost:8080`.

### Model Download Stalling / Slow
On first launch, the container downloads the ViT-Base checkpoint (~340 MB) from Hugging Face. Ensure your host machine has an active internet connection. You can check download progress via:
```bash
docker compose logs -f
```

### Missing API Keys
If no `SERPER_API_KEY` is provided, the container logs:
`[EVIDENCE_PROVIDER] Active Provider: WebSearchEvidenceProvider (Serper.dev: Using DuckDuckGo fallback)`
This is expected behavior and will not crash the container.

---

## 9. Security & Container Protections

- **Non-Root Execution**: Runs as unprivileged user `appuser` (UID `10001`).
- **No Privileged Mode**: Runs without host networking or elevated privileges.
- **SSRF Hardening**: Native domain validation prevents container from connecting to private/loopback metadata endpoints.
- **Health Checks**: Automated `HEALTHCHECK` periodically verifies service availability.
