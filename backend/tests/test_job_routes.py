"""
Unit tests for asynchronous job REST API routes.
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api.routes import router
from api.job_manager import _JOB_STORE

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_analyse_merchant_invalid_ssrf():
    """Verify SSRF-blocked URL returns 400 Bad Request."""
    payload = {
        "merchant_id": "m_test",
        "website_url": "http://127.0.0.1:8000",
    }
    response = client.post("/api/analyse-merchant", json=payload)
    assert response.status_code == 400
    assert "Invalid or restricted website URL" in response.json()["detail"]


@patch("api.routes.validate_url_security")
@patch("api.routes.JobManager.create_job")
def test_analyse_merchant_success(mock_create_job, mock_validate):
    """Verify valid merchant request creates job and returns 202 Accepted."""
    mock_validate.return_value = (True, "93.184.216.34", None)
    mock_create_job.return_value = "job_test_123"

    payload = {
        "merchant_id": "m_test_99",
        "website_url": "https://example.com",
        "claimed_brand": "Example",
    }
    response = client.post("/api/analyse-merchant", json=payload)
    assert response.status_code == 202
    assert response.json()["job_id"] == "job_test_123"
    assert response.json()["status"] == "QUEUED"


def test_get_job_status_not_found():
    """Verify 404 on non-existent job ID."""
    response = client.get("/api/analysis-jobs/non_existent_job")
    assert response.status_code == 404


def test_get_analysis_report_completed():
    """Verify report retrieval on completed job."""
    _JOB_STORE["job_completed_1"] = {
        "job_id": "job_completed_1",
        "merchant_id": "m_1",
        "website_url": "https://example.com",
        "status": "COMPLETED",
        "progress_message": "Complete",
        "created_at": time.time(),
        "updated_at": time.time(),
        "report": {"visual_risk_score": 15, "risk_level": "LOW"},
        "error": None,
        "listeners": [],
    }

    response = client.get("/api/analysis-jobs/job_completed_1/report")
    assert response.status_code == 200
    assert response.json()["visual_risk_score"] == 15
