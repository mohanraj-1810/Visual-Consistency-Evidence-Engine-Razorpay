"""
backend/tests/test_unreachable_domain.py — Hermetic Tests for Unreachable, Blocked, and Restricted Domains.
All tests use deterministic mocks to verify status classification, sub-score nullification,
and tailored claim generation without live network/DNS dependencies.
"""

import pytest
import sys
import requests
from pathlib import Path
from unittest.mock import MagicMock

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import crawler.site_crawler as sc
from crawler.site_crawler import crawl_merchant
from routes.analyze import execute_website_analysis
from scoring.fusion import calculate_text_business_risk, fuse_risk_scores


def test_dead_domain_returns_unverifiable(monkeypatch):
    """Verify that a non-resolving domain returns DNS_RESOLUTION_FAILED and UNVERIFIABLE."""
    dead_url = "https://demcet.ac.in"

    def mock_validate(url):
        return False, None, "DNS resolution failed for hostname 'demcet.ac.in'"

    monkeypatch.setattr(sc, "validate_url_security", mock_validate)

    # 1. Test crawler layer
    crawl_res = crawl_merchant(dead_url)
    assert crawl_res["crawl_successful"] is False
    assert crawl_res["crawl_status"] == "DNS_RESOLUTION_FAILED"
    assert crawl_res["error"] is not None

    # 2. Test text scoring layer
    text_risk = calculate_text_business_risk(crawl_res)
    assert text_risk["is_unverifiable"] is True
    assert text_risk["text_risk_score"] is None

    # 3. Test full pipeline execution
    analysis = execute_website_analysis(dead_url)
    fusion = analysis["fusion"]

    assert fusion["status"] == "UNVERIFIABLE"
    assert fusion["final_risk_score"] is None
    assert fusion["is_unverifiable"] is True
    assert "UNVERIFIABLE" in fusion["status_label"]
    assert fusion["badge_color"] != "#16a34a"  # Must NOT be green
    assert any("DNS" in r or "unreachable" in r.lower() for r in fusion["reasons"])


def test_fintech_domain_claim_not_ecommerce(monkeypatch):
    """Verify that non-ecommerce / fintech domains generate tailored non-catalog claims."""
    fintech_url = "https://razorpay.com"

    mock_crawl = {
        "crawl_successful": True,
        "crawl_status": "SUCCESS",
        "domain": "razorpay.com",
        "merchant_name": "Razorpay",
        "merchant_category": "fintech_payments",
        "products": [],
        "image_objects": [],
        "text_snippets": ["Razorpay Payment Gateway and Financial Services"],
        "error": None,
        "pages_crawled": 3,
        "emails": ["support@razorpay.com"],
        "phones": ["+91 80 1234 5678"],
        "policies_found": ["Privacy Policy", "Terms of Service"],
    }

    monkeypatch.setattr("routes.analyze.crawl_merchant", lambda url, **kwargs: mock_crawl)

    analysis = execute_website_analysis(fintech_url)
    claims = analysis["claims"]

    inventory_claim = claims.get("inventory_claim", "")
    assert "E-commerce product catalog" not in inventory_claim or "non-retail" in inventory_claim or "could not confirm" in inventory_claim


def test_robots_disallowed_returns_compliance_limited(monkeypatch):
    """Verify that robots.txt restriction triggers COMPLIANCE_LIMITED status and claim."""
    restricted_url = "https://www.nykaa.com"

    def mock_validate(url):
        return True, "93.184.216.34", None

    def mock_robots(url, user_agent="*"):
        return False  # Disallow crawler

    monkeypatch.setattr(sc, "validate_url_security", mock_validate)
    monkeypatch.setattr(sc, "_is_robots_allowed", mock_robots)

    crawl_res = crawl_merchant(restricted_url)
    assert crawl_res["crawl_successful"] is False
    assert crawl_res["crawl_status"] == "ROBOTS_DISALLOWED"

    analysis = execute_website_analysis(restricted_url)
    fusion = analysis["fusion"]
    claims = analysis["claims"]

    assert fusion["status"] == "COMPLIANCE_LIMITED"
    assert fusion["is_compliance_limited"] is True
    assert fusion["final_risk_score"] is None
    assert fusion["badge_color"] == "#3b82f6" or fusion["badge_color"] == "#2563eb"
    assert "COMPLIANCE-LIMITED" in fusion["status_label"]
    assert "robots.txt" in claims["inventory_claim"]
    assert "unreachable" not in claims["inventory_claim"].lower()


def test_bot_blocked_when_403_and_robots_allowed(monkeypatch):
    """
    Verify that when robots.txt ALLOWS crawling but the target server returns HTTP 403 (WAF),
    the crawler sets BOT_BLOCKED and generates anti-bot claim diagnostics.
    """
    waf_url = "https://waf-protected.example.com"

    def mock_validate(url):
        return True, "93.184.216.34", None

    def mock_robots(url, user_agent="*"):
        return True  # Robots.txt explicitly allows

    class Mock403Response:
        status_code = 403
        headers = {"server": "cloudflare", "content-type": "text/html"}
        text = "<html><title>403 Forbidden</title><body>Cloudflare Ray ID: Access Denied</body></html>"

        def raise_for_status(self):
            err = requests.exceptions.HTTPError("403 Client Error: Forbidden")
            err.response = self
            raise err

    def mock_get(self, url, *args, **kwargs):
        return Mock403Response()

    monkeypatch.setattr(sc, "validate_url_security", mock_validate)
    monkeypatch.setattr(sc, "_is_robots_allowed", mock_robots)
    monkeypatch.setattr(sc.SafeRedirectSession, "get", mock_get)

    crawl_res = crawl_merchant(waf_url)
    assert crawl_res["crawl_successful"] is False
    assert crawl_res["crawl_status"] == "BOT_BLOCKED"

    analysis = execute_website_analysis(waf_url)
    fusion = analysis["fusion"]
    claims = analysis["claims"]

    assert fusion["status"] == "BOT_BLOCKED"
    assert fusion["is_bot_blocked"] is True
    assert fusion["final_risk_score"] is None
    assert fusion["badge_color"] == "#6366f1"
    assert "ANTI-BOT" in fusion["status_label"] or "HTTP 403" in fusion["status_label"]
    assert "site blocked automated access" in claims["inventory_claim"]
    assert "unreachable" not in claims["inventory_claim"].lower()


def test_crawl_failure_all_subscores_are_null(monkeypatch):
    """Verify that when a website is unreachable, ALL sub-scores are explicitly null/N/A."""
    dead_url = "https://this-domain-does-not-exist-xyz123.com"

    def mock_validate(url):
        return False, None, "DNS resolution failed for hostname 'this-domain-does-not-exist-xyz123.com'"

    monkeypatch.setattr(sc, "validate_url_security", mock_validate)

    analysis = execute_website_analysis(dead_url)

    # 1. Top level fusion
    assert analysis["fusion"]["status"] == "UNVERIFIABLE"
    assert analysis["fusion"]["final_risk_score"] is None
    assert analysis["fusion"]["visual_risk_score"] is None
    assert analysis["fusion"]["text_risk_score"] is None
    assert analysis["fusion"]["identity_coherence"] is None
    assert analysis["fusion"]["tampering_score"] is None

    # 2. Sub-score objects
    assert analysis["visual_risk"]["visual_risk_score"] is None
    assert analysis["visual_risk"]["risk_level"] == "UNAVAILABLE"

    assert analysis["text_risk"]["text_risk_score"] is None

    assert analysis["identity"]["coherence_score"] is None
    assert analysis["identity"]["risk_level"] == "UNAVAILABLE"

    assert analysis["logo"]["similarity"] is None
    assert analysis["logo"]["consistency_score"] is None
    assert analysis["logo"]["inconsistency_risk"] is None
    assert analysis["logo"]["risk_level"] == "UNAVAILABLE"

    assert analysis["manipulation"]["manipulation_score"] is None
    assert analysis["manipulation"]["risk_level"] == "UNAVAILABLE"

    assert analysis["reuse"]["max_similarity"] is None
    assert analysis["reuse"]["reuse_risk_score"] is None
    assert analysis["reuse"]["risk_level"] == "UNAVAILABLE"

    # 3. No candidate or structured evidence generated for dead domain
    assert len(analysis["candidate_evidence"]) == 0
    assert len(analysis["structured_evidence"]) == 0
    assert analysis["forensic_target_image_base64"] is None


def test_redirect_limit_exceeded_sets_distinct_status_and_claims(monkeypatch):
    """Verify that exceeding redirect hops sets REDIRECT_LIMIT_EXCEEDED and tailored claims."""
    import requests

    loop_url = "https://redirect-loop-test.example.com"

    def mock_validate(url):
        return True, "93.184.216.34", None

    def mock_robots(url, user_agent="*"):
        return True

    def mock_get(self, url, *args, **kwargs):
        raise requests.exceptions.TooManyRedirects(
            "Exceeded maximum allowed redirects (3). Redirect chain: https://a.com -> https://b.com -> https://c.com -> https://d.com"
        )

    monkeypatch.setattr(sc, "validate_url_security", mock_validate)
    monkeypatch.setattr(sc, "_is_robots_allowed", mock_robots)
    monkeypatch.setattr(sc.SafeRedirectSession, "get", mock_get)

    # 1. Test crawler
    crawl_res = crawl_merchant(loop_url)
    assert crawl_res["crawl_successful"] is False
    assert crawl_res["crawl_status"] == "REDIRECT_LIMIT_EXCEEDED"
    assert "redirect" in crawl_res["error"].lower()

    # 2. Test full execute_website_analysis
    analysis = execute_website_analysis(loop_url)
    fusion = analysis["fusion"]
    claims = analysis["claims"]

    assert fusion["status"] == "REDIRECT_LIMIT_EXCEEDED"
    assert fusion["is_redirect_limit_exceeded"] is True
    assert fusion["final_risk_score"] is None
    assert fusion["badge_color"] == "#f59e0b"
    assert "REDIRECT SAFETY LIMIT EXCEEDED" in fusion["status_label"]

    # Assert claim text mentions redirect explicitly
    assert "redirect" in claims["inventory_claim"].lower()
    assert "redirect" in claims["compliance_claim"].lower()
    assert "safety limit of 3 hops" in claims["compliance_claim"]

    # Assert all sub-scores are explicitly null
    assert analysis["visual_risk"]["visual_risk_score"] is None
    assert analysis["identity"]["coherence_score"] is None
    assert analysis["logo"]["consistency_score"] is None
    assert analysis["manipulation"]["manipulation_score"] is None
    assert analysis["reuse"]["reuse_risk_score"] is None




