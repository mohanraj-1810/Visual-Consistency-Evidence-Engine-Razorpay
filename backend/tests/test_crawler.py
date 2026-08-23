"""Regression tests for merchant site crawler image classification."""

import sys
from pathlib import Path

from bs4 import BeautifulSoup

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from crawler.site_crawler import _extract_rich_images


def test_extract_rich_images_classifies_certificate_and_banner_without_nameerror():
    html = """
    <html><body>
<div class="artifact-image-grid">
      <img class="iso-cert-badge" src="/assets/iso-cert-badge.png" alt="ISO certification" />
      <img class="hero-banner-slider" src="/assets/hero-banner-slider.jpg" alt="Storefront hero" />
</div>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    image_objects, _logo = _extract_rich_images(soup, "https://shop.example.com")
    types_by_src = {img["src"]: img["asset_type"] for img in image_objects}
    assert types_by_src["https://shop.example.com/assets/iso-cert-badge.png"] == "certificate"
    assert types_by_src["https://shop.example.com/assets/hero-banner-slider.jpg"] == "banner"
