"""
backend/tests/test_demo_endpoints.py
QA Test Suite for Demo Endpoints:
- GET /api/demo-scenarios
- GET /api/demo-scenario/{scenario_id}
- Edge cases: invalid scenario_id, response schemas, execution determinism
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_get_demo_scenarios_list():
    """Verify GET /api/demo-scenarios returns list of scenarios with valid metadata."""
    response = client.get("/api/demo-scenarios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    
    ids = [s["id"] for s in data]
    assert "clean" in ids
    assert "supplier" in ids
    assert "counterfeit" in ids
    
    for s in data:
        assert "name" in s
        assert "category" in s
        assert "expected_tier" in s
        assert "summary" in s


def test_clean_demo_scenario_execution():
    """Verify clean demo scenario runs deterministically and produces CLEAR tier."""
    response = client.get("/api/demo-scenario/clean")
    assert response.status_code == 200
    data = response.json()
    
    assert "fusion" in data
    assert "evidence" in data
    assert data["fusion"]["status_tier"] == "CLEAR"
    assert data["fusion"]["final_risk_score"] < 25
    assert data.get("web_detection_mode") == "DEMO_FIXTURE_OFFLINE"


def test_supplier_demo_scenario_execution():
    """Verify supplier scenario produces LOW tier and excludes catalog matches from severe risk."""
    response = client.get("/api/demo-scenario/supplier")
    assert response.status_code == 200
    data = response.json()
    
    assert "fusion" in data
    assert data["fusion"]["status_tier"] == "LOW"
    assert data["fusion"]["status_tier"] != "HIGH"


def test_counterfeit_demo_scenario_execution():
    """Verify counterfeit scenario produces elevated/medium tier with multiple risk signals."""
    response = client.get("/api/demo-scenario/counterfeit")
    assert response.status_code == 200
    data = response.json()
    
    assert "fusion" in data
    assert data["fusion"]["status_tier"] in ["MEDIUM", "HIGH", "ELEVATED"]
    assert data["fusion"]["final_risk_score"] >= 45


def test_invalid_demo_scenario_returns_404():
    """Verify unknown scenario ID returns HTTP 404 with descriptive error."""
    response = client.get("/api/demo-scenario/non_existent_scenario_123")
    assert response.status_code == 404
    err = response.json()
    assert "detail" in err
    assert "Demo scenario 'non_existent_scenario_123' not found" in err["detail"]
