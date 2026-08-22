"""
candidate_search.py — Online Candidate Visual Evidence Discovery Orchestrator.
Searches public online sources for potential matching images/pages.
Production never falls back to local reference datasets.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from PIL import Image

from .provider import WebSearchEvidenceProvider, LocalReferenceEvidenceProvider


def discover_candidate_evidence(
    merchant_image: Optional[Image.Image] = None,
    query_hint: Optional[str] = None,
    category: Optional[str] = None,
    test_fixture_dir: Optional[Union[str, Path]] = None,
    max_candidates: int = 5,
) -> List[Dict[str, Any]]:
    """
    Discovers candidate public web images/pages for visual verification.

    Parameters
    ----------
    merchant_image : PIL Image of merchant product
    query_hint : Search query hint (merchant name, claim keywords, product title, alt text)
    category : Business category
    test_fixture_dir : Optional path for automated testing fixtures only (None in production)
    max_candidates : Maximum candidates to retrieve

    Returns
    -------
    List of candidate dicts with:
        image: PIL.Image
        source_url: str
        source_domain: str
        title: str
        source_type: 'ONLINE' | 'LOCAL_TEST_FIXTURE'
        candidate_id: str
    """
    # 1. In production, execute real online visual evidence search
    if test_fixture_dir is None:
        if not query_hint or len(query_hint.strip()) < 2:
            return []
        try:
            web_provider = WebSearchEvidenceProvider()
            online_results = web_provider.discover_candidates(
                query=query_hint,
                max_candidates=max_candidates,
                category=category,
            )
            return online_results[:max_candidates]
        except Exception:
            return []

    # 2. Automated test fixture path (when test_fixture_dir is explicitly provided by unit tests)
    ref_provider = LocalReferenceEvidenceProvider(test_fixture_dir)
    return ref_provider.discover_candidates(
        query=query_hint or "catalog",
        max_candidates=max_candidates,
        category=category,
    )[:max_candidates]
