"""
Unit tests for background analysis job manager and state transitions.
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch, AsyncMock
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api.job_manager import (
    JobManager,
    get_job,
    get_job_report,
    _JOB_STORE,
)


def test_job_store_retrieval_empty():
    """Verify non-existent job returns None."""
    assert get_job("non_existent_id") is None
    assert get_job_report("non_existent_id") is None


@pytest.mark.anyio
async def test_job_manager_create_and_listeners():
    """Verify job creation, state tracking, and listener notification."""
    with patch.object(JobManager, "_run_pipeline", new_callable=AsyncMock):
        job_id = JobManager.create_job(
            merchant_id="m_100",
            website_url="https://merchant-shop.com",
            claimed_brand="Shop",
        )

        job = get_job(job_id)
        assert job is not None
        assert job["merchant_id"] == "m_100"
        assert job["website_url"] == "https://merchant-shop.com"

        # Test registering and unregistering listener
        received_events = []

        def sample_listener(event):
            received_events.append(event)

        JobManager.register_listener(job_id, sample_listener)
        assert sample_listener in job["listeners"]

        await JobManager._emit_event(job_id, "TESTING", "Test message")
        assert len(received_events) == 1
        assert received_events[0]["status"] == "TESTING"
        assert received_events[0]["message"] == "Test message"

        JobManager.unregister_listener(job_id, sample_listener)
        assert sample_listener not in job["listeners"]


def test_cleanup_stale_jobs():
    """Verify old completed jobs are evicted based on TTL."""
    old_id = "old_completed_job"
    _JOB_STORE[old_id] = {
        "job_id": old_id,
        "status": "COMPLETED",
        "created_at": time.time() - 7200,
    }

    fresh_id = "fresh_active_job"
    _JOB_STORE[fresh_id] = {
        "job_id": fresh_id,
        "status": "QUEUED",
        "created_at": time.time(),
    }

    JobManager._cleanup_stale_jobs(ttl_seconds=3600)
    assert old_id not in _JOB_STORE
    assert fresh_id in _JOB_STORE
