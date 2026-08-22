"""
api/websockets.py — Real-Time WebSocket Progress Streaming.
Streams progress events and final report payloads to frontend dashboard analysts.
"""

from __future__ import annotations

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.job_manager import JobManager, get_job

router = APIRouter()


@router.websocket("/ws/analysis/{job_id}")
async def websocket_analysis_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket channel for streaming live job execution events to the risk analyst dashboard.
    """
    await websocket.accept()
    job = get_job(job_id)

    if not job:
        await websocket.send_text(json.dumps({
            "type": "error",
            "job_id": job_id,
            "message": f"Job '{job_id}' not found.",
        }))
        await websocket.close()
        return

    # If job is already completed or failed, send immediate status
    if job.get("status") in ("COMPLETED", "FAILED"):
        await websocket.send_text(json.dumps({
            "type": "progress",
            "job_id": job_id,
            "status": job.get("status"),
            "message": job.get("progress_message"),
            "data": job.get("report") if job.get("status") == "COMPLETED" else None,
        }))
        await websocket.close()
        return

    # Send initial status
    await websocket.send_text(json.dumps({
        "type": "progress",
        "job_id": job_id,
        "status": job.get("status"),
        "message": job.get("progress_message"),
    }))

    async def on_event(event_payload: dict):
        try:
            await websocket.send_text(json.dumps(event_payload))
        except Exception:
            pass

    # Register listener
    JobManager.register_listener(job_id, on_event)

    try:
        while True:
            # Keep connection open until client disconnects or pipeline completes
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        JobManager.unregister_listener(job_id, on_event)
