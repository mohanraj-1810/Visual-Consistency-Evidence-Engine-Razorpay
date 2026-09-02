"""
Unit tests for evidence normalization, domain filtering, and marketplace classification.
"""

import sys
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.evidence_normalizer import (
    _extract_domain,
    _clean_domain_str,
    is_self_referencing_domain,
    is_marketplace_domain,
    is_stock_domain,
    is_supplier_domain,
    normalize_web_detection_evidence,
)


def test_domain_extraction_and_cleaning():
    """Verify domain extractor strips protocols, ports, and subdomains correctly."""
    assert _extract_domain("https://www.example.com/products/item1.html") == "example.com"
    assert _extract_domain("http://store.shop.co.uk:8080/path") == "store.shop.co.uk"
    assert _extract_domain("") == ""

    assert _clean_domain_str("https://WWW.MyStore.com/") == "mystore.com"


def test_is_self_referencing_domain():
    """Verify detection of self-domain matches."""
    assert is_self_referencing_domain("mystore.com", "mystore.com") is True
    assert is_self_referencing_domain("cdn.mystore.com", "mystore.com") is True
    assert is_self_referencing_domain("otherstore.com", "mystore.com") is False
    assert is_self_referencing_domain("", "mystore.com") is False


def test_is_marketplace_and_stock_domain():
    """Verify classification of marketplaces and stock photography hosts."""
    assert is_marketplace_domain("amazon.com") is True
    assert is_marketplace_domain("aliexpress.com") is True
    assert is_marketplace_domain("independent-boutique.com") is False

    assert is_stock_domain("shutterstock.com") is True
    assert is_stock_domain("pinterest.com") is True
    assert is_stock_domain("independent-boutique.com") is False


def test_is_supplier_domain():
    """Verify identification of wholesale supplier domains."""
    assert is_supplier_domain("alibaba.com") is True
    assert is_supplier_domain("global-wholesale-distributor.net") is True
    assert is_supplier_domain("local-coffee-shop.com") is False


def test_normalize_web_detection_evidence():
    """Verify transformation of raw web detection data into structured evidence."""
    item_result = {
        "meta": {"src": "https://merchant.com/product.jpg", "asset_type": "product_image"},
        "web_detection": {
            "full_matching_images": [{"url": "https://external-store.com/item.jpg"}],
            "pages_with_matching_images": [{"url": "https://external-store.com/listing"}],
        },
    }

    evidence = normalize_web_detection_evidence(item_result, merchant_domain="merchant.com")
    assert evidence is not None
    assert evidence["asset_url"] == "https://merchant.com/product.jpg"
    assert evidence["signal_type"] == "external_image_reuse"
    assert evidence["score"] > 0
