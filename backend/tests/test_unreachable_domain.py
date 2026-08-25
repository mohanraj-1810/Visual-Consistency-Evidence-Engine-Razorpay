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


