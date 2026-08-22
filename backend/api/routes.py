"""
api/routes.py — REST API Endpoints for Asynchronous Visual Risk Analysis.
Provides POST /api/analyse-merchant, GET /api/analysis-jobs/{job_id}, and
GET /api/analysis-jobs/{job_id}/report.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.job_manager import JobManager, get_job, get_job_report
from crawler.ssrf_validator import validate_url_security

router = APIRouter()


class AnalyseMerchantRequest(BaseModel):
    merchant_id: str = Field(..., description="Unique merchant identifier (e.g. merchant_001)")
    website_url: str = Field(..., description="Merchant website URL to crawl and analyse")
    claimed_brand: Optional[str] = Field(None, description="Optional self-reported brand or business name")
    merchant_category: Optional[str] = Field("general", description="Merchant business category")


class EnqueueResponse(BaseModel):
    job_id: str
    status: str


@router.post("/api/analyse-merchant", response_model=EnqueueResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyse_merchant(payload: AnalyseMerchantRequest):
    """
    Submits a merchant website URL for asynchronous visual risk analysis.
    Returns immediately with a job_id and QUEUED status.
    """
    url = payload.website_url.strip()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="website_url cannot be empty.",
        )

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Pre-validate URL for SSRF protection before enqueuing
    is_safe, _, err_msg = validate_url_security(url)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or restricted website URL: {err_msg}",
        )

    job_id = JobManager.create_job(
        merchant_id=payload.merchant_id,
        website_url=url,
        claimed_brand=payload.claimed_brand,
        merchant_category=payload.merchant_category,
    )

    return {"job_id": job_id, "status": "QUEUED"}


@router.get("/api/analysis-jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Polls the current execution status of an analysis job.
    Status values: QUEUED, CRAWLING, EXTRACTING_IMAGES, SEARCHING_WEB, ANALYSING_FORENSICS, SCORING, COMPLETED, FAILED.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job '{job_id}' not found.",
        )

    return {
        "job_id": job["job_id"],
        "merchant_id": job["merchant_id"],
        "website_url": job["website_url"],
        "status": job["status"],
        "progress_message": job.get("progress_message"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "error": job.get("error"),
    }


@router.get("/api/analysis-jobs/{job_id}/report")
async def get_analysis_report(job_id: str):
    """
    Retrieves the final visual risk intelligence report for a completed job.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job '{job_id}' not found.",
        )

    if job.get("status") == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis job failed: {job.get('error', 'Unknown pipeline failure')}",
        )

    if job.get("status") != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_425_TOO_EARLY,
            detail=f"Analysis job is still in progress (current status: {job.get('status')}).",
        )

    report = get_job_report(job_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job completed but report was not found.",
        )

    return report
