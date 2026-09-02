# Changelog

All notable changes to the **Visual Consistency Evidence Engine** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-09-02

### Added
- **CI/CD Automation:** Added GitHub Actions workflows (`.github/workflows/ci.yml`) for multi-version Python testing (3.10, 3.11, 3.12), Flake8 linting, and Vite frontend build verification.
- **Security Auditing:** Added Bandit static application security testing workflow (`.github/workflows/security.yml`).
- **Code Quality Tooling:** Added centralized `.pre-commit-config.yaml` and `pyproject.toml` configurations for `black`, `isort`, `flake8`, `pytest`, and `coverage`.
- **SSRF Protection Test Suite:** Added unit test suite `backend/tests/test_ssrf_validator.py` covering RFC1918 private IPs, loopback addresses, cloud metadata endpoints, and DNS rebinding protections.
- **Image Forensics Test Suite:** Added unit tests `backend/tests/test_manipulation.py` for Error Level Analysis (ELA), Laplacian gradient anomaly detection, and synthetic/AI generation estimators.
- **Image Reuse Detection Tests:** Added unit tests `backend/tests/test_image_reuse.py` for reference catalog caching and batch similarity scoring.
- **ViT Embeddings Test Suite:** Added unit tests `backend/tests/test_vit_embeddings.py` for cosine similarity, vector dimension mismatch handling, and embedding normalization.
- **Job Manager & Streaming Tests:** Added unit tests `backend/tests/test_job_manager.py` and `backend/tests/test_websockets.py` for async job lifecycle and WebSocket progress streaming.
- **Scoring & Fusion Tests:** Added unit tests `backend/tests/test_scoring_fusion.py` for weight normalization, E1/E4 separation, and multi-signal corroboration amplification.
- **System Documentation:** Added `docs/ARCHITECTURE.md`, `docs/API_SPECIFICATION.md`, and `docs/TESTING_GUIDE.md`.

---

## [1.1.0] - 2026-08-15

### Added
- Online visual candidate discovery via Serper Google Lens API.
- Claim-to-evidence reasoning engine with structured evidence objects.
- Forensic manipulation heatmap generation.
- Verified brand logo resolver and ViT brand consistency checker.

### Changed
- Refactored visual risk scorer to require 2+ corroborating vectors before elevating to HIGH risk.
- Strengthened robots.txt compliance during automated storefront crawling.

---

## [1.0.0] - 2026-07-01

### Added
- Initial release of Visual Consistency Evidence Engine.
- Multi-modal visual feature extraction and cosine similarity search.
- Interactive React/Vite analyst dashboard with real-time WebSocket progress.
