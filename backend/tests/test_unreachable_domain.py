import pytest
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from crawler.site_crawler import crawl_merchant
from routes.analyze import execute_website_analysis, run_pipeline
from scoring.fusion import calculate_text_business_risk, fuse_risk_scores


def test_dead_domain_returns_unverifiable():
    # Test guaranteed non-resolving domain
    dead_url = "https://demcet.ac.in"
    
    # 1. Test crawler layer
    crawl_res = crawl_merchant(dead_url)
    assert crawl_res["crawl_successful"] is False
    assert crawl_res["crawl_status"] in ["DNS_RESOLUTION_FAILED", "UNREACHABLE", "CONNECTION_REFUSED", "TIMEOUT"]
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
    assert "Unreachable" in fusion["reasons"][0] or "DNS" in fusion["reasons"][0] or "unreachable" in fusion["reasons"][0].lower()


def test_fintech_domain_claim_not_ecommerce():
    # Test razorpay.com classification and claim generation
    analysis = execute_website_analysis("https://razorpay.com")
    claims = analysis["claims"]
    
    inventory_claim = claims.get("inventory_claim", "")
    # Must NOT claim to be an e-commerce product catalog
    assert "E-commerce product catalog" not in inventory_claim or "non-retail" in inventory_claim or "could not confirm" in inventory_claim


def test_robots_disallowed_returns_compliance_limited():
    # Test robots-restricted domain (Nykaa disallows bots)
    analysis = execute_website_analysis("https://www.nykaa.com")
    fusion = analysis["fusion"]
    claims = analysis["claims"]

    assert fusion["status"] == "COMPLIANCE_LIMITED"
    assert fusion["is_compliance_limited"] is True
    assert fusion["final_risk_score"] is None
    assert fusion["badge_color"] == "#2563eb"
    assert "COMPLIANCE-LIMITED" in fusion["status_label"]
    assert "robots.txt" in claims["inventory_claim"]
    assert "unreachable" not in claims["inventory_claim"].lower()


def test_etsy_bot_blocked_returns_bot_blocked():
    # Test WAF/anti-bot protected domain (Etsy returns HTTP 403)
    analysis = execute_website_analysis("https://www.etsy.com")
    fusion = analysis["fusion"]
    claims = analysis["claims"]

    assert fusion["status"] == "BOT_BLOCKED"
    assert fusion["is_bot_blocked"] is True
    assert fusion["final_risk_score"] is None
    assert fusion["badge_color"] == "#6366f1"
    assert "ANTI-BOT" in fusion["status_label"] or "HTTP 403" in fusion["status_label"]
    assert "site blocked automated access" in claims["inventory_claim"]
    assert "unreachable" not in claims["inventory_claim"].lower()


def test_crawl_failure_all_subscores_are_null():
    """Verify that when a website is unreachable, ALL sub-scores are explicitly null/N/A."""
    dead_url = "https://this-domain-does-not-exist-xyz123.com"
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
    from unittest.mock import MagicMock

    loop_url = "https://redirect-loop-test.example.com"

    def mock_validate(url):
        return True, "93.184.216.34", None

    def mock_robots(url, user_agent="*"):
        return True

    def mock_get(self, url, *args, **kwargs):
        raise requests.exceptions.TooManyRedirects(
            "Exceeded maximum allowed redirects (3). Redirect chain: https://a.com -> https://b.com -> https://c.com -> https://d.com"
        )

    # Patch crawler dependencies
    import crawler.site_crawler as sc
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



