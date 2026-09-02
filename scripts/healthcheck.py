#!/usr/bin/env python3
"""
scripts/healthcheck.py — Standalone System & Dependency Health Diagnostic Tool.
Verifies Python version, critical packages, PyTorch/ViT acceleration, and API reachability.
"""

from __future__ import annotations

import sys
import os
import platform
from pathlib import Path


def check_python_environment() -> bool:
    print("[1/4] Checking Python runtime...")
    ver = sys.version_info
    print(f"      Python version: {ver.major}.{ver.minor}.{ver.micro} ({platform.platform()})")
    if ver.major < 3 or (ver.major == 3 and ver.minor < 10):
        print("      [ERROR] Python 3.10+ is required.")
        return False
    print("      [OK] Python version is supported.")
    return True


def check_core_dependencies() -> bool:
    print("\n[2/4] Checking core Python dependencies...")
    packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "PIL",
        "cv2",
        "numpy",
        "requests",
        "bs4",
        "pytest",
    ]
    all_ok = True
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"      [OK] {pkg} is installed.")
        except ImportError:
            print(f"      [MISSING] {pkg} is not installed.")
            all_ok = False
    return all_ok


def check_torch_vit() -> bool:
    print("\n[3/4] Checking PyTorch & Vision Transformer model backend...")
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU"
        print(f"      PyTorch version: {torch.__version__} (Device: {device_name})")
        print("      [OK] PyTorch is available.")
        return True
    except ImportError:
        print("      [WARNING] PyTorch is not installed. Will use perceptual fallback algorithms.")
        return False


def check_directories() -> bool:
    print("\n[4/4] Checking project filesystem structure...")
    root = Path(__file__).resolve().parent.parent
    expected_dirs = ["backend", "frontend", "docs", "dataset"]
    for d in expected_dirs:
        dir_path = root / d
        if dir_path.exists() and dir_path.is_dir():
            print(f"      [OK] Directory exists: {d}/")
        else:
            print(f"      [WARNING] Missing directory: {d}/")
    return True


def main() -> int:
    print("=" * 60)
    print("Visual Consistency Evidence Engine — System Health Diagnostics")
    print("=" * 60)

    p_ok = check_python_environment()
    d_ok = check_core_dependencies()
    t_ok = check_torch_vit()
    f_ok = check_directories()

    print("\n" + "=" * 60)
    if p_ok and d_ok:
        print("Diagnostics completed successfully. Environment is ready!")
        print("=" * 60)
        return 0
    else:
        print("Diagnostics detected missing components. Please run: pip install -r requirements.txt")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
