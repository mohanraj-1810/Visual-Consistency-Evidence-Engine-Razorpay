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
from PIL import Image

from crawler.site_crawler import crawl_merchant
from crawler.image_extractor import process_and_prioritize_images
from services.web_image_search import get_vision_client, batch_search_images
from services.evidence_fusion import fuse_asset_evidence, index_analyzed_assets
from services.logo_detector import verify_merchant_logo
from services.forensic_heatmap import run_forensic_tampering_analysis
from services.visual_risk_scorer import calculate_visual_risk


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
    def create_job(
        merchant_id: str,
        website_url: str,
        claimed_brand: Optional[str] = None,
        merchant_category: Optional[str] = "general",
    ) -> str:
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
            claimed_brand = job["claimed_brand"]

            try:
                # ── Step 1: CRAWLING ──
                await JobManager._emit_event(job_id, "CRAWLING", f"Crawling merchant website: {url}")
                loop = asyncio.get_running_loop()
                crawl_data = await loop.run_in_executor(None, crawl_merchant, url, 5)

                if crawl_data.get("blocked"):
                    raise ValueError(f"Crawling blocked by security policy: {crawl_data.get('error')}")

                merchant_domain = crawl_data.get("domain", "")

                # ── Step 2: EXTRACTING_IMAGES ──
                await JobManager._emit_event(job_id, "EXTRACTING_IMAGES", "Extracting, classifying, and prioritizing visual assets...")
                img_objects = crawl_data.get("image_objects", [])
                merchant_name = claimed_brand or crawl_data.get("merchant_name") or "Merchant"

                proc_data = await loop.run_in_executor(
                    None,
                    process_and_prioritize_images,
                    img_objects,
                    merchant_name,
                    8,
                )

                rep_images = proc_data.get("representative_images", [])
                num_extracted = len(rep_images)
                await JobManager._emit_event(job_id, "EXTRACTING_IMAGES", f"Extracted {num_extracted} representative images.")

                # ── Step 3: SEARCHING_WEB & DUAL EVIDENCE FUSION ──
                await JobManager._emit_event(job_id, "SEARCHING_WEB", "Searching web matches & querying local ViT platform index...")
                vision_client, analysis_mode = get_vision_client()

                batch_results = await batch_search_images(
                    rep_images,
                    client=vision_client,
                    mode=analysis_mode,
                )

                # Fuse evidence for each asset (Google Vision + local ViT cross-merchant)
                evidence_list: List[Dict[str, Any]] = []
                for b in batch_results:
                    meta = b.get("meta", {})
                    img = b.get("image")
                    web_res = b.get("web_detection", {})
                    fused_item = fuse_asset_evidence(
                        asset_image=img,
                        meta=meta,
                        web_detection_result=web_res,
                        current_merchant_id=merchant_id,
                        current_domain=merchant_domain,
                    )
                    evidence_list.append(fused_item)

                # ── Step 4: ANALYSING_FORENSICS & LOGO ──
                await JobManager._emit_event(job_id, "ANALYSING_FORENSICS", "Analysing logo consistency and digital tampering...")
                
                # Extract any detected brand logos from Vision annotations
                detected_logos_list = []
                for b in batch_results:
                    w_res = b.get("web_detection", {})
                    if isinstance(w_res, dict) and w_res.get("logos"):
                        detected_logos_list.extend(w_res.get("logos", []))

                # Check logo
                logo_img = proc_data.get("logo_image")
                logo_url = crawl_data.get("logo_url")
                brand_status, logo_evidence = verify_merchant_logo(
                    logo_img,
                    logo_url,
                    claimed_brand,
                    detected_logos=detected_logos_list if detected_logos_list else None,
                )
                if logo_evidence:
                    # Append default provenance fields to logo evidence
                    logo_evidence.setdefault("google_web_match_score", 0)
                    logo_evidence.setdefault("local_vit_similarity_score", logo_evidence.get("score", 0))
                    logo_evidence.setdefault("google_vision_provider_result", "none")
                    logo_evidence.setdefault("vit_cosine_similarity", 0.0)
                    logo_evidence.setdefault("matched_domains", [])
                    logo_evidence.setdefault("matched_merchant_ids", [])
                    logo_evidence.setdefault("masked_merchant_ids", [])
                    logo_evidence.setdefault("evidence_source", "LOCAL_INDEX")
                    logo_evidence.setdefault("corroborated", False)
                    logo_evidence.setdefault("confidence", "HIGH" if brand_status == "VERIFIED" else "LOW")
                    logo_evidence.setdefault("asset_evidence_level", "POTENTIAL_REUSE" if logo_evidence.get("score", 0) > 40 else "LOW_EVIDENCE")
                    evidence_list.append(logo_evidence)

                # Check certificates / tampering
                cert_images = proc_data.get("certificate_images", [])
                if cert_images:
                    for idx, c_img in enumerate(cert_images[:2]):
                        score, manip_evidence = run_forensic_tampering_analysis(c_img, f"certificate_{idx+1}", "certificate")
                        if manip_evidence and score > 0:
                            manip_evidence.setdefault("google_web_match_score", 0)
                            manip_evidence.setdefault("local_vit_similarity_score", 0)
                            manip_evidence.setdefault("google_vision_provider_result", "none")
                            manip_evidence.setdefault("vit_cosine_similarity", 0.0)
                            manip_evidence.setdefault("matched_domains", [])
                            manip_evidence.setdefault("matched_merchant_ids", [])
                            manip_evidence.setdefault("masked_merchant_ids", [])
                            manip_evidence.setdefault("evidence_source", "LOCAL_INDEX")
                            manip_evidence.setdefault("corroborated", False)
                            manip_evidence.setdefault("confidence", "HIGH" if score >= 50 else "MEDIUM")
                            manip_evidence.setdefault("asset_evidence_level", "POTENTIAL_REUSE" if score >= 35 else "LOW_EVIDENCE")
                            evidence_list.append(manip_evidence)

                # ── Step 5: SCORING & FUSION ──
                await JobManager._emit_event(job_id, "SCORING", "Calculating visual risk score and safety recommendations...")
                visual_risk_score, risk_level, recommended_action = calculate_visual_risk(
                    evidence_list,
                    brand_verification_status=brand_status,
                )

                # ── Step 6: COMPLETED (Report Construction) ──
                clean_evidence = []
                for e in evidence_list:
                    clean_evidence.append({
                        "asset_url": e.get("asset_url", ""),
                        "asset_type": e.get("asset_type", "product_image"),
                        "signal_type": e.get("signal_type", "external_image_reuse"),
                        "score": e.get("score", 0),
                        "google_web_match_score": e.get("google_web_match_score", 0),
                        "local_vit_similarity_score": e.get("local_vit_similarity_score", 0),
                        "google_vision_provider_result": e.get("google_vision_provider_result", "none"),
                        "vit_cosine_similarity": e.get("vit_cosine_similarity", 0.0),
                        "matched_domains": e.get("matched_domains", []),
                        "matched_merchant_ids": e.get("matched_merchant_ids", []),
                        "masked_merchant_ids": e.get("masked_merchant_ids", []),
                        "evidence_source": e.get("evidence_source", "FUSED"),
                        "corroborated": e.get("corroborated", False),
                        "confidence": e.get("confidence", "LOW"),
                        "asset_evidence_level": e.get("asset_evidence_level", "LOW_EVIDENCE"),
                        "matched_pages": e.get("matched_pages", []),
                        "matched_images": e.get("matched_images", []),
                        "explanation": e.get("explanation", ""),
                        "heatmap_url": e.get("heatmap_url"),
                    })

                final_report = {
                    "job_id": job_id,
                    "merchant_id": merchant_id,
                    "website_url": url,
                    "images_scanned": num_extracted,
                    "visual_risk_score": visual_risk_score,
                    "risk_level": risk_level,
                    "recommended_action": recommended_action,
                    "brand_verification_status": brand_status,
                    "analysis_mode": analysis_mode,
                    "evidence": clean_evidence,
                }

                job["report"] = final_report

                # ── Step 7: Post-Analysis ViT Indexing ──
                # Strictly index newly scanned assets AFTER report generation
                index_analyzed_assets(
                    assets_with_images=rep_images,
                    merchant_id=merchant_id,
                    domain=merchant_domain,
                )

                await JobManager._emit_event(
                    job_id,
                    "COMPLETED",
                    f"Risk score completed: {visual_risk_score}/100 ({risk_level} — {recommended_action})",
                    data=final_report,
                )

            except Exception as e:
                job["error"] = str(e)
                await JobManager._emit_event(job_id, "FAILED", f"Analysis failed: {str(e)}")
