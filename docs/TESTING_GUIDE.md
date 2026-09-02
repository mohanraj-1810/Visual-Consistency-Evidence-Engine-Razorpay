# Developer Testing Guide

This guide describes how to run automated unit tests, integration tests, and code quality linters for the **Visual Consistency Evidence Engine**.

---

## 1. Running the Test Suite

Execute the entire test suite via `pytest`:

```bash
# Run all unit and integration tests
python -m pytest

# Run with verbose output and test execution timings
python -m pytest -v --durations=10

# Run specific test module
python -m pytest backend/tests/test_visual_risk_scorer.py
```

---

## 2. Test Coverage Reporting

To calculate line and branch coverage across backend modules:

```bash
python -m pytest --cov=backend --cov-report=term-missing --cov-report=html
```

HTML reports will be generated in `htmlcov/index.html`.

---

## 3. Code Style & Static Analysis

We enforce PEP8 compliance, strict formatting, and security audits:

```bash
# Run Flake8 linter
flake8 backend --max-line-length=120

# Check Black formatting
black --check backend

# Check isort import ordering
isort --check-only backend

# Run Bandit security audit
bandit -r backend -ll -x backend/tests,backend/venv
```

---

## 4. Test Directory Layout

```
backend/tests/
├── test_automated_engine.py       # End-to-end evaluation dataset tests
├── test_candidate_search.py       # Online evidence search & fallback tests
├── test_crawler.py                # Merchant site HTML & asset extraction tests
├── test_demo_endpoints.py         # REST API endpoint verification
├── test_evidence_fusion.py        # Multi-modal fusion & scoring tests
├── test_forensic_heatmap.py       # ELA tampering & heatmap rendering tests
├── test_logo_detector.py          # ViT brand logo alignment tests
├── test_reasoning.py              # Structured evidence synthesis & claims reasoning
├── test_serper_evidence.py        # Serper Google Lens API integration tests
├── test_unreachable_domain.py     # DNS & network edge case tests
└── test_visual_risk_scorer.py     # Risk thresholding & corroboration rules
```
