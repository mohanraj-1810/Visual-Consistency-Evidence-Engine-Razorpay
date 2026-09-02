"""
Unit tests for real-time WebSocket progress streaming endpoint.
"""

import sys
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api.websockets import router as ws_router
from api.job_manager import _JOB_STORE

test_app = FastAPI()
test_app.include_router(ws_router)


def test_websocket_job_not_found():
    """Verify connecting to non-existent job sends error and closes."""
    client = TestClient(test_app)
    with client.websocket_connect("/ws/analysis/missing_job_123") as ws:
        data = ws.receive_text()
        payload = json.loads(data)
        assert payload["type"] == "error"
        assert "not found" in payload["message"]


def test_websocket_completed_job_immediate_payload():
    """Verify connecting to already-completed job sends report payload immediately."""
    _JOB_STORE["comp_job_456"] = {
        "job_id": "comp_job_456",
        "status": "COMPLETED",
        "progress_message": "Analysis completed: LOW",
        "report": {"visual_risk_score": 10},
        "listeners": [],
    }

    client = TestClient(test_app)
    with client.websocket_connect("/ws/analysis/comp_job_456") as ws:
        data = ws.receive_text()
        payload = json.loads(data)
        assert payload["type"] == "progress"
        assert payload["status"] == "COMPLETED"
        assert payload["data"] == {"visual_risk_score": 10}


def test_websocket_ping_pong_heartbeat():
    """Verify ping message receives pong response."""
    _JOB_STORE["active_job_789"] = {
        "job_id": "active_job_789",
        "status": "CRAWLING",
        "progress_message": "Crawling...",
        "report": None,
        "listeners": [],
    }

    client = TestClient(test_app)
    with client.websocket_connect("/ws/analysis/active_job_789") as ws:
        # Initial message
        init_data = ws.receive_text()
        assert json.loads(init_data)["status"] == "CRAWLING"

        # Send ping
        ws.send_text(json.dumps({"type": "ping"}))
        pong_data = ws.receive_text()
        pong_payload = json.loads(pong_data)
        assert pong_payload["type"] == "pong"
        assert pong_payload["job_id"] == "active_job_789"
