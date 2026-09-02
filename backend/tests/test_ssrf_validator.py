"""
Unit tests for SSRF URL validation and IP address blocking engine.
"""

import sys
from pathlib import Path
from unittest.mock import patch
import socket
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from crawler.ssrf_validator import is_ip_blocked, validate_url_security


def test_is_ip_blocked_private_and_loopback():
    """Verify standard private RFC1918 and loopback IPs are blocked."""
    # Loopback
    assert is_ip_blocked("127.0.0.1") is True
    assert is_ip_blocked("127.0.1.1") is True
    assert is_ip_blocked("::1") is True

    # RFC 1918 Private
    assert is_ip_blocked("10.0.0.1") is True
    assert is_ip_blocked("172.16.0.1") is True
    assert is_ip_blocked("192.168.1.1") is True

    # Cloud metadata
    assert is_ip_blocked("169.254.169.254") is True

    # Invalid / Malformed IP strings
    assert is_ip_blocked("invalid_ip") is True
    assert is_ip_blocked("999.999.999.999") is True


def test_is_ip_blocked_public_ips():
    """Verify legitimate public routable IPs are not blocked."""
    assert is_ip_blocked("8.8.8.8") is False
    assert is_ip_blocked("1.1.1.1") is False
    assert is_ip_blocked("142.250.190.46") is False


def test_validate_url_security_invalid_scheme():
    """Verify unsupported protocols are blocked."""
    is_valid, ip, err = validate_url_security("ftp://example.com/file.txt")
    assert is_valid is False
    assert "Unsupported URL scheme" in err

    is_valid, ip, err = validate_url_security("file:///etc/passwd")
    assert is_valid is False
    assert "Unsupported URL scheme" in err


def test_validate_url_security_blocked_hostnames():
    """Verify direct localhost and cloud metadata hostnames are blocked."""
    is_valid, ip, err = validate_url_security("http://localhost:8000/api")
    assert is_valid is False
    assert "Access to blocked hostname" in err

    is_valid, ip, err = validate_url_security("http://metadata.google.internal/computeMetadata/v1")
    assert is_valid is False
    assert "Access to blocked hostname" in err


@patch("crawler.ssrf_validator.socket.getaddrinfo")
def test_validate_url_security_resolving_private_ip(mock_getaddrinfo):
    """Verify DNS resolving to internal IP is rejected."""
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.50", 80))
    ]

    is_valid, ip, err = validate_url_security("http://internal-portal.corp")
    assert is_valid is False
    assert ip == "192.168.1.50"
    assert "private or restricted network" in err


@patch("crawler.ssrf_validator.socket.getaddrinfo")
def test_validate_url_security_valid_public_domain(mock_getaddrinfo):
    """Verify valid public web domain passes SSRF validation."""
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
    ]

    is_valid, ip, err = validate_url_security("https://example.com/shop")
    assert is_valid is True
    assert ip == "93.184.216.34"
    assert err is None
