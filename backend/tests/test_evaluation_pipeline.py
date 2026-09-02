"""
Unit tests for evaluation benchmark framework and metrics processing.
"""

import sys
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from evaluation.evaluate_pipeline import ORIGINAL_18_CASE_IDS


def test_original_case_ids_structure():
    """Verify evaluation case manifest has expected clean, borderline, and high-risk case IDs."""
    assert len(ORIGINAL_18_CASE_IDS) >= 12
    assert any("clean" in cid for cid in ORIGINAL_18_CASE_IDS)
    assert any("bord" in cid for cid in ORIGINAL_18_CASE_IDS)
