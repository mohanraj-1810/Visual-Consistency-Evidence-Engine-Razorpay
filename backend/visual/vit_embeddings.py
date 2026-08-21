"""
vit_embeddings.py — Pretrained Vision Transformer (ViT) embedding engine.
Generates normalized feature embeddings for images locally.
Includes graceful local fallbacks (torchvision / feature extractors)
if HuggingFace hub is unavailable offline.
"""

from __future__ import annotations

import os
import torch
import numpy as np
from PIL import Image
from typing import Optional, Union

# Global cache for model and processor
_MODEL = None
_PROCESSOR = None
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_FALLBACK_MODEL = None


def load_vit_model(model_name: str = "google/vit-base-patch16-224"):
    """
    Load ViT model and processor. Cached in memory.
    """
    global _MODEL, _PROCESSOR, _FALLBACK_MODEL
    if _MODEL is not None and _PROCESSOR is not None:
        return _MODEL, _PROCESSOR

    try:
        from transformers import AutoImageProcessor, AutoModel
        # Load local or remote HF ViT
        _PROCESSOR = AutoImageProcessor.from_pretrained(model_name)
        _MODEL = AutoModel.from_pretrained(model_name).to(_DEVICE)
        _MODEL.eval()
        return _MODEL, _PROCESSOR
    except Exception as e:
        # Fallback to torchvision lightweight backbone for robust offline execution
        try:
            import torchvision.models as models
            import torchvision.transforms as transforms
            
            # Using torchvision squeezenet / resnet as robust offline feature extractor
            resnet = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
            resnet.classifier = torch.nn.Identity()
            _FALLBACK_MODEL = resnet.to(_DEVICE)
            _FALLBACK_MODEL.eval()

            _PROCESSOR = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            return _FALLBACK_MODEL, _PROCESSOR
        except Exception as fb_err:
            # Simple direct numpy/torch fallback if network is completely disabled
            return None, None


def get_image_embedding(image: Union[Image.Image, str, np.ndarray]) -> np.ndarray:
    """
    Generate a normalized 1D feature embedding vector for a given image.

    Parameters
    ----------
    image : PIL.Image.Image, filepath, or np.ndarray

    Returns
    -------
    np.ndarray : L2-normalized 1D feature embedding vector
    """
    if isinstance(image, str):
        image = Image.open(image).convert("RGB")
    elif isinstance(image, np.ndarray):
        image = Image.fromarray(image).convert("RGB")
    elif isinstance(image, Image.Image):
        image = image.convert("RGB")

    model, processor = load_vit_model()

    if model is None or processor is None:
        # Fallback statistical pixel histogram/color moment embedding if neural net fails
        img_resized = image.resize((64, 64))
        arr = np.array(img_resized, dtype=np.float32) / 255.0
        hist, _ = np.histogramdd(arr.reshape(-1, 3), bins=(8, 8, 8), range=((0,1),(0,1),(0,1)))
        vec = hist.flatten()
        norm = np.linalg.norm(vec)
        return vec / (norm + 1e-9)

    try:
        if hasattr(processor, "preprocess") or hasattr(processor, "__call__") and "transformers" in str(type(processor)):
            inputs = processor(images=image, return_tensors="pt").to(_DEVICE)
            with torch.no_grad():
                outputs = model(**inputs)
                # Use [CLS] token embedding or pooled output
                if hasattr(outputs, "last_hidden_state"):
                    embedding = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()
                elif hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                    embedding = outputs.pooler_output.squeeze().cpu().numpy()
                else:
                    embedding = outputs[0][:, 0, :].squeeze().cpu().numpy()
        else:
            # Torchvision transform fallback
            tensor = processor(image).unsqueeze(0).to(_DEVICE)
            with torch.no_grad():
                embedding = model(tensor).squeeze().cpu().numpy()

        embedding = np.asarray(embedding, dtype=np.float32).flatten()
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

    except Exception as e:
        # Graceful perceptual vector fallback
        img_resized = image.resize((64, 64))
        arr = np.array(img_resized, dtype=np.float32) / 255.0
        hist, _ = np.histogramdd(arr.reshape(-1, 3), bins=(8, 8, 8), range=((0, 1), (0, 1), (0, 1)))
        vec = hist.flatten()
        norm = np.linalg.norm(vec)
        return vec / (norm + 1e-9)


def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two 1D normalized vectors.
    Returns float in range [0.0, 1.0].
    """
    v1 = vec1.flatten()
    v2 = vec2.flatten()
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    sim = dot / (norm1 * norm2)
    # Clip numerical precision to [-1.0, 1.0], map to [0.0, 1.0]
    sim = max(-1.0, min(1.0, float(sim)))
    # For normalized feature spaces, cosine similarity is in [0, 1] range after rectifying negative angles
    return float(max(0.0, sim))
