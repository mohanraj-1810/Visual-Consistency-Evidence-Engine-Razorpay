# ==============================================================================
# Stage 1: Build React/Vite Frontend
# ==============================================================================
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy source code and build production distribution
COPY frontend/ ./
RUN npm run build

# ==============================================================================
# Stage 2: Python Application Runtime
# ==============================================================================
FROM python:3.12-slim

# Set environment variables for Python & Model Cache
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/cache/huggingface \
    TORCH_HOME=/app/cache/torch \
    PYTHONPATH=/app/backend:/app

WORKDIR /app

# Install system dependencies (curl for healthcheck, libglib for image/vision utils)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (CPU-optimized PyTorch first for fast downloads & compact image)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt

# Copy application directories and code
COPY backend/ ./backend/
COPY dataset/ ./dataset/
COPY evaluation/ ./evaluation/
COPY app.py ./
COPY test_pipeline.py ./

# Copy compiled frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create persistent cache and results directories
RUN mkdir -p /app/cache/huggingface /app/cache/torch /app/results

# Create non-root application user for container security
RUN useradd -u 10001 -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose backend & integrated frontend service port
EXPOSE 8000

# Native health check against FastAPI /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the FastAPI application server
CMD ["python", "backend/main.py", "--host", "0.0.0.0", "--port", "8000"]
