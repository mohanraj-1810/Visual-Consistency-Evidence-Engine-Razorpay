"""
demo_real_crawl.py - Real-World Crawl Evidence Demo Script
===========================================================
Runs the existing crawler (crawler/site_crawler.py) + ViT visual pipeline
against 3 real public storefront/marketplace pages and saves the output to
results/real_crawl_demo.json.

This output is SEPARATE from the scored synthetic evaluation set and is
intended to be shown live during the hackathon demo to demonstrate the
pipeline working on real-world data.

Target URLs (all public, no auth required, robots.txt allows crawling):
  1. https://books.toscrape.com/       -- canonical scraping test site (book store)
  2. https://scrapethissite.com/pages/simple/  -- scraping sandbox
  3. https://webscraper.io/test-sites/e-commerce/allinone -- e-commerce test site

Usage:
    python demo_real_crawl.py
    python demo_real_crawl.py --urls "https://example.com" "https://another.com"
    python demo_real_crawl.py --out results/my_crawl.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---- path bootstrap -------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
for p in [str(BACKEND_DIR), str(REPO_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("demo_real_crawl")

# Default public demo targets - chosen because they explicitly allow crawlers
# and are designed as scraping/testing sandboxes.
DEFAULT_URLS: List[str] = [
    "https://books.toscrape.com/",
    "https://webscraper.io/test-sites/e-commerce/allinone",
    "https://scrapethissite.com/pages/simple/",
]

OUTPUT_PATH = REPO_ROOT / "results" / "real_crawl_demo.json"


def _truncate_text(s: str, max_chars: int = 500) -> str:
    return s[:max_chars] + "..." if len(s) > max_chars else s


def crawl_and_analyse(url: str, idx: int, total: int) -> Dict[str, Any]:
    """Crawls a single URL and runs the full ViT pipeline. Returns a summary dict."""
    from crawler.site_crawler import crawl_merchant
    from crawler.image_extractor import process_and_prioritize_images, download_image
    from visual.vit_embeddings import load_vit_model
    from online_evidence.candidate_search import discover_candidate_evidence
    from online_evidence.verifier import verify_candidates_with_vit
    from PIL import Image

    print(f"\n{'='*70}")
    print(f"[{idx}/{total}] Crawling: {url}")
    print("="*70)

    crawl_start = time.time()
    crawl_data = crawl_merchant(url)
    crawl_elapsed = round((time.time() - crawl_start) * 1000, 1)

    pages = crawl_data.get("pages_crawled", [])
    images_raw = crawl_data.get("image_objects", [])
    print(f"  OK Pages crawled:  {len(pages)}")
    print(f"  OK Raw images:     {len(images_raw)}")
    print(f"  OK Crawl latency:  {crawl_elapsed}ms")
    if crawl_data.get("error"):
        print(f"  WARNING Crawler error: {crawl_data['error']}")

    merchant_name = crawl_data.get("merchant_name", "Demo Merchant")
    proc = process_and_prioritize_images(images_raw, merchant_name=merchant_name, max_representatives=3)
    product_images = [img for img, _ in proc["representative_images"]]
    logo_image = proc.get("logo_image")

    if logo_image is None and crawl_data.get("logo_url"):
        logo_image = download_image(crawl_data["logo_url"])

    if not product_images:
        product_images = [Image.new("RGB", (224, 224), (200, 200, 200))]

    print(f"  OK Selected representative images: {len(product_images)}")

    load_vit_model()

    query_hint = f"{merchant_name} product"
    evidence_start = time.time()
    candidate_evidence = discover_candidate_evidence(
        merchant_image=product_images[0],
        query_hint=query_hint,
        max_candidates=3,
    )
    evidence_elapsed = round((time.time() - evidence_start) * 1000, 1)
    print(f"  OK Candidate evidence found: {len(candidate_evidence)} (in {evidence_elapsed}ms)")

    merchant_domain = crawl_data.get("domain")
    if product_images and candidate_evidence:
        verified = verify_candidates_with_vit(
            product_images[0], candidate_evidence, merchant_domain=merchant_domain
        )
    else:
        verified = {
            "max_similarity": 0.0,
            "evidence_strength": "LOW",
            "match_status": "NO_EXTERNAL_MATCH",
            "is_own_brand_candidate": True,
            "explanation": "No product images or candidates available.",
        }

    match_status = verified.get("match_status", "UNKNOWN")
    max_sim = verified.get("max_similarity", 0.0)
    print(f"  OK ViT match status: {match_status}  (max cosine sim: {max_sim:.3f})")

    total_elapsed = round((time.time() - crawl_start) * 1000, 1)

    return {
        "url": url,
        "domain": crawl_data.get("domain"),
        "merchant_name": merchant_name,
        "title": crawl_data.get("title", ""),
        "description": _truncate_text(crawl_data.get("description", ""), 300),
        "pages_crawled": pages,
        "raw_image_count": len(images_raw),
        "representative_image_count": len(product_images),
        "products_found": len(crawl_data.get("products", [])),
        "has_contact": crawl_data.get("has_contact"),
        "has_policy": crawl_data.get("has_policy"),
        "has_about": crawl_data.get("has_about"),
        "social_links": crawl_data.get("social_links", []),
        "logo_url": crawl_data.get("logo_url"),
        "candidate_evidence_count": len(candidate_evidence),
        "vit_match_status": match_status,
        "vit_max_similarity": round(float(max_sim), 4),
        "vit_is_own_brand": verified.get("is_own_brand_candidate", True),
        "vit_explanation": verified.get("explanation", ""),
        "crawler_error": crawl_data.get("error"),
        "latency_ms": {
            "crawl": crawl_elapsed,
            "evidence_search": evidence_elapsed,
            "total": total_elapsed,
        },
    }


def main(urls=None, out_path=None):
    target_urls = urls or DEFAULT_URLS
    output_file = out_path or OUTPUT_PATH

    print("\n" + "="*70)
    print("  REAL-WORLD CRAWL EVIDENCE DEMO")
    print(f"  Targets: {len(target_urls)} public URLs")
    print(f"  Output:  {output_file}")
    print("="*70)

    results = []
    errors = []

    for i, url in enumerate(target_urls, 1):
        try:
            result = crawl_and_analyse(url, i, len(target_urls))
            results.append(result)
        except Exception as exc:
            logger.error("Failed on %s: %s", url, exc, exc_info=True)
            errors.append({"url": url, "error": str(exc)})

    payload = {
        "run_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": (
            "Real-world crawl evidence - produced by the live crawler + ViT pipeline "
            "against public URLs. Separate from the synthetic 18-case evaluation set."
        ),
        "targets_attempted": len(target_urls),
        "targets_succeeded": len(results),
        "results": results,
        "errors": errors,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"  DONE! {len(results)}/{len(target_urls)} succeeded.")
    print(f"  Saved to: {output_file}")
    print("="*70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Real-world crawl evidence demo - runs crawler + ViT on public URLs"
    )
    parser.add_argument("--urls", nargs="+", default=None, metavar="URL",
                        help="URLs to crawl (defaults to 3 public sandbox sites)")
    parser.add_argument("--out", default=None, metavar="PATH",
                        help=f"Output JSON path (default: {OUTPUT_PATH})")
    args = parser.parse_args()
    out = Path(args.out) if args.out else None
    main(urls=args.urls, out_path=out)
