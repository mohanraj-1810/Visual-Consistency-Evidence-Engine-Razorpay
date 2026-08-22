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
    Discovers real-world online visual candidates via public web endpoints.
    Never uses hardcoded fake data or local reference datasets.
    """

    def __init__(self, timeout: int = _REQUEST_TIMEOUT):
        self.timeout = timeout

    def discover_candidates(
        self,
        query: str,
        max_candidates: int = 4,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not query or len(query.strip()) < 2:
            return []

        search_query = query.strip()
        if category:
            search_query = f"{search_query} {category}"

        candidates: List[Dict[str, Any]] = []

        try:
            # 1. Search public web results via DuckDuckGo HTML endpoint
            search_url = "https://html.duckduckgo.com/html/"
            payload = {"q": search_query}
            resp = requests.post(search_url, data=payload, headers=_HEADERS, timeout=self.timeout)
            
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                
                results = soup.find_all("div", class_=re.compile(r"result|results_links"))
                for idx, res in enumerate(results[:max_candidates * 2]):
                    link_tag = res.find("a", class_=re.compile(r"result__url|result__snippet|result__a"))
                    if not link_tag:
                        continue
                    raw_href = link_tag.get("href", "")
                    title_text = link_tag.get_text(strip=True)
                    
                    # Parse target URL
                    actual_url = raw_href
                    if "uddg=" in raw_href:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                        if "uddg" in parsed and parsed["uddg"]:
                            actual_url = parsed["uddg"][0]
                            
                    if not actual_url.startswith("http"):
                        continue

                    domain = urllib.parse.urlparse(actual_url).netloc
                    if not domain:
                        continue

                    # Extract candidate thumbnail image if present in snippet
                    img_tag = res.find("img")
                    img_src = img_tag.get("src") if img_tag else None
                    candidate_img = None
                    
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

                    if candidate_img is not None:
                        candidates.append({
                            "image": candidate_img,
                            "source_url": actual_url,
                            "source_domain": domain,
                            "title": title_text or f"Public web match on {domain}",
                            "source_type": "ONLINE",
                            "candidate_id": f"web_{idx}_{domain}",
                        })
                        
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
