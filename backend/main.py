"""
backend/main.py — FastAPI Application Entrypoint.
Provides REST API endpoints for Visual Consistency & Evidence Engine.
"""

from __future__ import annotations

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from visual.vit_embeddings import load_vit_model
from routes.analyze import router as analyze_router


# Ensure utf-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Pre-warm Vision Transformer backbone
    print("[INIT] Pre-warming Vision Transformer model...")
    try:
        load_vit_model()
        print("[SUCCESS] Vision Transformer model pre-warmed successfully.")
    except Exception as e:
        print(f"[WARN] Model pre-warm notice: {e}")
    yield
    print("[INFO] Shutting down Visual Consistency Engine.")


app = FastAPI(
    title="Visual Consistency & Evidence Engine API",
    description="Multimodal merchant risk decision-support system for human risk analysts.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# For production deployment, uncomment and configure your frontend domain:
# origins.append("https://your-deployed-frontend-url.com")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(analyze_router, prefix="", tags=["Risk Analysis"])


@app.get("/health")
async def health_check():
    """Service health and readiness check."""
    return {
        "status": "healthy",
        "service": "Visual Consistency & Evidence Engine",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
