"""
Unit tests for online candidate visual evidence search orchestrator.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from online_evidence.candidate_search import discover_candidate_evidence


def test_discover_candidate_evidence_empty_query():
    """Verify that an empty or whitespace query safely returns an empty list without crashing."""
    assert discover_candidate_evidence(query_hint="") == []
    assert discover_candidate_evidence(query_hint=" ") == []
    assert discover_candidate_evidence(query_hint="a") == []


@patch("online_evidence.candidate_search.WebSearchEvidenceProvider")
def test_discover_candidate_evidence_online_success(mock_provider_cls):
    """Verify that valid online search calls the web provider and limits results."""
    mock_instance = MagicMock()
    mock_results = [
        {"candidate_id": f"c_{i}", "source_domain": f"domain{i}.com", "source_url": f"https://domain{i}.com/p{i}.jpg"}
        for i in range(10)
    ]
    mock_instance.discover_candidates.return_value = mock_results
    mock_provider_cls.return_value = mock_instance

    results = discover_candidate_evidence(
        query_hint="Urban Distributor Fashion",
        category="apparel",
        max_candidates=3,
    )

    assert len(results) == 3
    assert results[0]["candidate_id"] == "c_0"
    mock_instance.discover_candidates.assert_called_once_with(
        query="Urban Distributor Fashion",
        max_candidates=3,
        category="apparel",
    )


@patch("online_evidence.candidate_search.WebSearchEvidenceProvider")
def test_discover_candidate_evidence_exception_fallback(mock_provider_cls):
    """Verify that network or provider exceptions are caught gracefully and return empty list."""
    mock_instance = MagicMock()
    mock_instance.discover_candidates.side_effect = RuntimeError("Network timeout")
    mock_provider_cls.return_value = mock_instance

    results = discover_candidate_evidence(query_hint="Test Product", max_candidates=5)
    assert results == []


@patch("online_evidence.candidate_search.LocalReferenceEvidenceProvider")
def test_discover_candidate_evidence_fixture_path(mock_ref_cls, tmp_path):
    """Verify that test_fixture_dir routes to local reference provider."""
    mock_instance = MagicMock()
    mock_results = [{"candidate_id": "f_1", "source_domain": "fixture.local"}]
    mock_instance.discover_candidates.return_value = mock_results
    mock_ref_cls.return_value = mock_instance

    results = discover_candidate_evidence(
        query_hint="Mock Query",
        test_fixture_dir=tmp_path,
        max_candidates=2,
    )

    mock_ref_cls.assert_called_once_with(tmp_path)
    assert len(results) == 1
    assert results[0]["candidate_id"] == "f_1"
