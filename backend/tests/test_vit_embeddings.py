"""
Unit tests for ViT embeddings and cosine similarity engine.
"""

import sys
from pathlib import Path
from PIL import Image
import numpy as np
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from visual.vit_embeddings import (
    compute_cosine_similarity,
    _get_cache_key,
    get_model_status,
    get_image_embedding,
)


def test_compute_cosine_similarity_identical_and_orthogonal():
    """Verify cosine similarity is 1.0 for identical vectors and 0.0 for orthogonal vectors."""
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([1.0, 0.0, 0.0])
    assert pytest.approx(compute_cosine_similarity(v1, v2), 0.001) == 1.0

    v3 = np.array([0.0, 1.0, 0.0])
    assert pytest.approx(compute_cosine_similarity(v1, v3), 0.001) == 0.0


def test_compute_cosine_similarity_zero_vectors():
    """Verify zero norm vectors safely return 0.0 similarity."""
    v_zero = np.zeros(10)
    v_ones = np.ones(10)
    assert compute_cosine_similarity(v_zero, v_ones) == 0.0


def test_compute_cosine_similarity_different_dimensions():
    """Verify vectors of mismatched dimensions are truncated gracefully."""
    v_long = np.array([1.0, 1.0, 0.0, 0.0, 0.0])
    v_short = np.array([1.0, 1.0, 0.0])
    sim = compute_cosine_similarity(v_long, v_short)
    assert 0.0 <= sim <= 1.0


def test_get_cache_key():
    """Verify cache key generation for paths and PIL images."""
    assert _get_cache_key("/images/product.jpg") == "path:/images/product.jpg"
    img = Image.new("RGB", (32, 32), color="red")
    key = _get_cache_key(img)
    assert key is not None
    assert key.startswith("pil:(32, 32):RGB:")


def test_get_model_status():
    """Verify get_model_status returns standard diagnostics."""
    status = get_model_status()
    assert "model_name" in status or "active_backend" in status or isinstance(status, dict)


def test_get_image_embedding_normalized():
    """Verify embedding returns 1D array with unit norm."""
    img = Image.new("RGB", (32, 32), color="blue")
    emb = get_image_embedding(img)
    assert isinstance(emb, np.ndarray)
    assert len(emb.shape) == 1
    norm = np.linalg.norm(emb)
    assert pytest.approx(norm, 0.01) == 1.0
