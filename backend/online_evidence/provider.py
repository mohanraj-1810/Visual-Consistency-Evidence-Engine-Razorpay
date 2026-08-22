"""
provider.py — Provider Abstraction for Visual Evidence Discovery.
Production strictly uses WebSearchEvidenceProvider.
LocalReferenceEvidenceProvider is preserved solely as a controlled test fixture.
"""

from __future__ import annotations

import io
import re
import urllib.parse
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from PIL import Image
import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_REQUEST_TIMEOUT = 4  # seconds


class BaseEvidenceProvider(ABC):
    """Abstract interface for candidate visual evidence discovery."""

    @abstractmethod
    def discover_candidates(
        self,
        query: str,
        max_candidates: int = 4,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Discover candidate public visual assets.

        Returns
        -------
        List of dicts:
            {
                "image": PIL.Image.Image,
                "source_url": str,
                "source_domain": str,
                "title": str,
                "source_type": "ONLINE" | "LOCAL_TEST_FIXTURE",
                "candidate_id": str,
            }
        """
        pass


class WebSearchEvidenceProvider(BaseEvidenceProvider):
    """
    Discovers real-world online visual candidates via public web endpoints or commercial APIs.
    Supports Serper.dev, SerpApi, and Google Custom Search Engine if API keys are set in the environment.
    Uses concurrent thread pools for fast parallel candidate fetching and image downloads.
    """

    def __init__(self, timeout: int = _REQUEST_TIMEOUT):
        self.timeout = timeout

    def _fetch_candidate_details(self, idx: int, actual_url: str, title_text: str, domain: str, img_src: Optional[str]) -> Optional[Dict[str, Any]]:
        """Helper to fetch and parse candidate webpage or download its image in parallel."""
        candidate_img = None
        
        # 1. Try downloading snippet thumbnail if present
        if img_src:
            if img_src.startswith("//"):
                img_src = "https:" + img_src
            if img_src.startswith("http"):
                try:
                    img_resp = requests.get(img_src, headers=_HEADERS, timeout=2)
                    if img_resp.status_code == 200 and len(img_resp.content) > 200:
                        candidate_img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
                except Exception:
                    pass

        # 2. Fallback: Scrape the target URL's webpage for OG image or first large img
        if candidate_img is None and actual_url.startswith("http"):
            try:
                page_resp = requests.get(actual_url, headers=_HEADERS, timeout=3, allow_redirects=True)
                if page_resp.status_code == 200:
                    from bs4 import BeautifulSoup
                    page_soup = BeautifulSoup(page_resp.text, "html.parser")
                    
                    # Try OpenGraph image first (usually high-quality product photo)
                    og = page_soup.find("meta", property="og:image")
                    if og and og.get("content"):
                        img_url = og["content"].strip()
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        if img_url.startswith("http"):
                            try:
                                ir = requests.get(img_url, headers=_HEADERS, timeout=2)
                                if ir.status_code == 200 and len(ir.content) > 500:
                                    candidate_img = Image.open(io.BytesIO(ir.content)).convert("RGB")
                            except Exception:
                                pass
                                
                    # Try first large image tag on page if OG fails
                    if candidate_img is None:
                        for img_tag in page_soup.find_all("img", src=True)[:4]:
                            fallback_src = img_tag["src"]
                            if fallback_src.startswith("//"):
                                fallback_src = "https:" + fallback_src
                            if not fallback_src.startswith("http"):
                                continue
                            try:
                                ir = requests.get(fallback_src, headers=_HEADERS, timeout=2)
                                if ir.status_code == 200 and len(ir.content) > 2000:
                                    candidate_img = Image.open(io.BytesIO(ir.content)).convert("RGB")
                                    break
                            except Exception:
                                continue
            except Exception:
                pass

        if candidate_img is not None:
            return {
                "image": candidate_img,
                "source_url": actual_url,
                "source_domain": domain,
                "title": title_text or f"Public web match on {domain}",
                "source_type": "ONLINE",
                "candidate_id": f"web_{idx}_{domain}",
            }
        return None

    def discover_candidates(
        self,
        query: str,
        max_candidates: int = 4,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        import os
        from concurrent.futures import ThreadPoolExecutor, as_completed

        if not query or len(query.strip()) < 2:
            return []

        search_query = query.strip()
        if category:
            search_query = f"{search_query} {category}"

        raw_results = []

        # ── 1. Commercial API Integration (Enterprise Grade) ───────────────────
        serper_key = os.environ.get("SERPER_API_KEY")
        serpapi_key = os.environ.get("SERPAPI_API_KEY")
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        google_cse_id = os.environ.get("GOOGLE_CSE_ID")

        if serper_key:
            # Serper.dev Google Search API
            try:
                headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
                payload = json.dumps({"q": search_query, "num": max_candidates * 2})
                resp = requests.post("https://google.serper.dev/search", headers=headers, data=payload, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("organic", []):
                        raw_results.append({
                            "url": item.get("link"),
                            "title": item.get("title"),
                            "img_src": item.get("imageUrl") or (item.get("images", [{}])[0].get("url") if item.get("images") else None)
                        })
            except Exception:
                pass

        elif serpapi_key:
            # SerpApi integration
            try:
                params = {"q": search_query, "api_key": serpapi_key, "num": max_candidates * 2}
                resp = requests.get("https://serpapi.com/search", params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("organic_results", []):
                        raw_results.append({
                            "url": item.get("link"),
                            "title": item.get("title"),
                            "img_src": item.get("thumbnail")
                        })
            except Exception:
                pass

        elif google_api_key and google_cse_id:
            # Official Google CSE Engine
            try:
                params = {"q": search_query, "key": google_api_key, "cx": google_cse_id, "num": max_candidates * 2}
                resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("items", []):
                        img_src = None
                        metatags = item.get("pagemap", {}).get("metatags", [{}])[0]
                        if metatags:
                            img_src = metatags.get("og:image") or metatags.get("twitter:image")
                        raw_results.append({
                            "url": item.get("link"),
                            "title": item.get("title"),
                            "img_src": img_src
                        })
            except Exception:
                pass

        # ── 2. Highly Robust Scraping Fallback ────────────────────────────────
        if not raw_results:
            try:
                search_url = "https://html.duckduckgo.com/html/"
                payload = {"q": search_query}
                resp = requests.post(search_url, data=payload, headers=_HEADERS, timeout=self.timeout)
                
                if resp.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, "html.parser")
                    results = soup.find_all("div", class_=re.compile(r"result|results_links"))
                    for res in results[:max_candidates * 2]:
                        link_tag = res.find("a", class_=re.compile(r"result__url|result__snippet|result__a"))
                        if not link_tag:
                            continue
                        raw_href = link_tag.get("href", "")
                        title_text = link_tag.get_text(strip=True)
                        
                        actual_url = raw_href
                        if "uddg=" in raw_href:
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                            if "uddg" in parsed and parsed["uddg"]:
                                actual_url = parsed["uddg"][0]
                                
                        if not actual_url.startswith("http"):
                            continue

                        img_tag = res.find("img")
                        img_src = img_tag.get("src") if img_tag else None
                        
                        raw_results.append({
                            "url": actual_url,
                            "title": title_text,
                            "img_src": img_src
                        })
            except Exception:
                pass

        if not raw_results:
            return []

        # ── 3. Parallel Processing of Candidates (Diamond Upgrade) ──────────────
        candidates: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=min(8, len(raw_results))) as executor:
            futures = []
            for idx, res in enumerate(raw_results):
                actual_url = res["url"]
                domain = urllib.parse.urlparse(actual_url).netloc
                if not domain:
                    continue
                futures.append(
                    executor.submit(
                        self._fetch_candidate_details,
                        idx,
                        actual_url,
                        res["title"],
                        domain,
                        res.get("img_src")
                    )
                )

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        candidates.append(result)
                        if len(candidates) >= max_candidates:
                            break
                except Exception:
                    pass

        return candidates[:max_candidates]


class LocalReferenceEvidenceProvider(BaseEvidenceProvider):
    """
    Test fixture provider for unit and regression testing only.
    Strictly NOT used in the production pipeline.
    """

    def __init__(self, reference_dir: Union[str, Path]):
        self.reference_dir = Path(reference_dir)

    def discover_candidates(
        self,
        query: str,
        max_candidates: int = 4,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not self.reference_dir.exists():
            return []

        valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        ref_files = [f for f in self.reference_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_exts]

        candidates: List[Dict[str, Any]] = []
        for idx, f in enumerate(ref_files[:max_candidates]):
            try:
                img = Image.open(f).convert("RGB")
                clean_name = f.stem.replace("_", "-").lower()
                mock_domain = f"catalog-archive.internal/{clean_name}"
                mock_url = f"https://archive.merchant-catalog.org/assets/{f.name}"
                candidates.append({
                    "image": img,
                    "source_url": mock_url,
                    "source_domain": mock_domain,
                    "title": f"Catalog Reference: {f.name}",
                    "source_type": "LOCAL_TEST_FIXTURE",
                    "candidate_id": f"local_ref_{idx}_{f.stem}",
                    "local_path": str(f),
                    "filename": f.name,
                })
            except Exception:
                continue

        return candidates
