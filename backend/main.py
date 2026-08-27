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
from api.routes import router as async_api_router
from api.websockets import router as ws_router
from services.web_image_search import get_vision_status


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
    
    # Log Google Cloud Vision status
    v_stat = get_vision_status()
    print(f"[VISION] Google Cloud Vision Mode: {v_stat['analysis_mode']} (Key Configured: {v_stat['api_key_configured']})")
    
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
app.include_router(async_api_router, prefix="", tags=["Async Merchant Analysis"])
app.include_router(ws_router, prefix="", tags=["WebSockets"])


@app.get("/health")
async def health_check():
    """Service health and readiness check."""
    return {
        "status": "healthy",
        "service": "Visual Consistency & Evidence Engine",
        "version": "1.0.0",
        "vision_intelligence": get_vision_status(),
    }


@app.get("/vision/status")
async def vision_status():
    """Google Cloud Vision API configuration, credential, and cache status."""
    return {
        "status": "ok",
        "vision_intelligence": get_vision_status(),
    }


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(
        description="🛡️ Visual Consistency & Evidence Engine — Backend API Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host IP address to bind the API server")
    parser.add_argument("--port", type=int, default=8000, help="Port number for the API server")
    # BUG-006 FIX: Default reload to False (production-safe). Use --reload explicitly for development.
    parser.add_argument("--reload", action="store_true", default=False, help="Enable auto-reload on code changes (development only)")
    parser.add_argument("--no-reload", dest="reload", action="store_false", help="Disable auto-reload (default)")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")

    args = parser.parse_args()

    # BUG-006 FIX: uvicorn does not support reload=True with workers > 1.
    # Disable reload automatically when multiple workers are requested.
    if args.reload and args.workers > 1:
        print("[WARN] --reload is incompatible with --workers > 1. Disabling reload for multi-worker mode.")
        args.reload = False

    print("=" * 70)
    print(" 🛡️  Visual Consistency & Evidence Engine — API Server")
    print("=" * 70)
    print(f" • Server URL:         http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}")
    print(f" • Interactive Docs:   http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/docs")
    print(f" • Health Endpoint:    http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/health")
    print(f" • Auto-Reload:        {'Enabled' if args.reload else 'Disabled'}")
    print("=" * 70)

    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload, workers=args.workers)

