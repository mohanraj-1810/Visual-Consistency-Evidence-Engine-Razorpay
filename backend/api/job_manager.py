"""
api/job_manager.py — Asynchronous Job Queue and Real-Time State Manager.
Handles background pipeline execution, status transitions, concurrency control,
and live event broadcasting.
"""

from __future__ import annotations

import uuid
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable

from routes.analyze import execute_website_analysis


# Thread-safe in-memory store for analysis jobs and reports
# job_id -> { status, progress_message, created_at, report, error, listeners }
_JOB_STORE: Dict[str, Dict[str, Any]] = {}
_MAX_CONCURRENT_JOBS = 4
_JOB_SEMAPHORE = asyncio.Semaphore(_MAX_CONCURRENT_JOBS)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves job state by job_id."""
    return _JOB_STORE.get(job_id)


def get_job_report(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves completed final report for a job_id."""
    job = _JOB_STORE.get(job_id)
    if job and job.get("status") == "COMPLETED":
        return job.get("report")
    return None


class JobManager:
    """Manages creation, execution, and event subscription of visual risk analysis jobs."""

    @staticmethod
    def _cleanup_stale_jobs(ttl_seconds: int = 3600):
        """Evicts jobs older than TTL to manage memory efficiently."""
        now = time.time()
        stale_ids = [
            jid for jid, j in _JOB_STORE.items()
            if now - j.get("created_at", now) > ttl_seconds and j.get("status") in ("COMPLETED", "FAILED")
        ]
        for jid in stale_ids:
            _JOB_STORE.pop(jid, None)

    @staticmethod
    def create_job(
        merchant_id: str,
        website_url: str,
        claimed_brand: Optional[str] = None,
        merchant_category: Optional[str] = "general",
    ) -> str:
        JobManager._cleanup_stale_jobs()
        job_id = f"job_{uuid.uuid4().hex[:10]}"
        _JOB_STORE[job_id] = {
            "job_id": job_id,
            "merchant_id": merchant_id,
            "website_url": website_url,
            "claimed_brand": claimed_brand,
            "merchant_category": merchant_category,
            "status": "QUEUED",
            "progress_message": "Job enqueued in background pipeline.",
            "created_at": time.time(),
            "updated_at": time.time(),
            "report": None,
            "error": None,
            "listeners": [],
        }

        # Launch background task
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(JobManager._run_pipeline(job_id))
        except RuntimeError:
            import threading
            threading.Thread(target=lambda: asyncio.run(JobManager._run_pipeline(job_id)), daemon=True).start()
        return job_id

    @staticmethod
    def register_listener(job_id: str, callback: Callable[[Dict[str, Any]], Any]):
        job = _JOB_STORE.get(job_id)
        if job:
            job["listeners"].append(callback)

    @staticmethod
    def unregister_listener(job_id: str, callback: Callable[[Dict[str, Any]], Any]):
        job = _JOB_STORE.get(job_id)
        if job and callback in job["listeners"]:
            job["listeners"].remove(callback)

    @staticmethod
    async def _emit_event(job_id: str, status: str, message: str, data: Optional[Dict[str, Any]] = None):
        job = _JOB_STORE.get(job_id)
        if not job:
            return
        job["status"] = status
        job["progress_message"] = message
        job["updated_at"] = time.time()

        payload = {
            "type": "progress",
            "job_id": job_id,
            "status": status,
            "message": message,
            "timestamp": time.time(),
            "data": data,
        }

        # Notify active WebSocket listeners
        for listener in list(job["listeners"]):
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(payload)
                else:
                    listener(payload)
            except Exception:
                pass

    @staticmethod
    async def _run_pipeline(job_id: str):
        async with _JOB_SEMAPHORE:
            job = _JOB_STORE.get(job_id)
            if not job:
                return

            merchant_id = job["merchant_id"]
            url = job["website_url"]

            loop = asyncio.get_running_loop()

            def progress_callback(step_id: str, message: str):
                status_map = {
                    "crawl": "CRAWLING",
                    "extract": "EXTRACTING_IMAGES",
                    "prioritize": "EXTRACTING_IMAGES",
                    "search": "SEARCHING_WEB",
                    "candidates": "SEARCHING_WEB",
                    "vit": "SEARCHING_WEB",
                    "logo": "ANALYSING_FORENSICS",
                    "reuse": "ANALYSING_FORENSICS",
                    "manipulation": "ANALYSING_FORENSICS",
                    "identity": "ANALYSING_FORENSICS",
                    "fusion": "SCORING",
                }
                status = status_map.get(step_id, step_id.upper())
                try:
                    asyncio.run_coroutine_threadsafe(
                        JobManager._emit_event(job_id, status, message),
                        loop,
                    )
                except Exception:
                    pass

            try:
                await JobManager._emit_event(job_id, "CRAWLING", f"Crawling merchant website: {url}")
                analysis_result = await loop.run_in_executor(
                    None,
                    execute_website_analysis,
                    url,
                    progress_callback,
                )

                # Attach job metadata to final report payload
                analysis_result["job_id"] = job_id
                analysis_result["merchant_id"] = merchant_id
                analysis_result["website_url"] = url

                job["report"] = analysis_result

                fusion = analysis_result.get("fusion", {})
                risk_score = fusion.get("final_risk_score")
                status_label = fusion.get("status_label", fusion.get("status", "COMPLETED"))

                score_msg = (
                    f"Risk score completed: {risk_score}/100 ({status_label})"
                    if risk_score is not None
                    else f"Analysis completed: {status_label}"
                )

                await JobManager._emit_event(
                    job_id,
                    "COMPLETED",
                    score_msg,
                    data=analysis_result,
                )

            except Exception as e:
                job["error"] = str(e)
                await JobManager._emit_event(job_id, "FAILED", f"Analysis failed: {str(e)}")
