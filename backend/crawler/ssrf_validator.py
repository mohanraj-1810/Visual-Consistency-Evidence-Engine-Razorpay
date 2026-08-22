"""
crawler/ssrf_validator.py — SSRF Protection and URL Security Validator.
Guarantees requests only connect to public routable internet hosts.
Prevents internal network port scanning, cloud metadata access, and DNS rebinding.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple, Optional


_BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network
    ipaddress.ip_network("10.0.0.0/8"),         # RFC 1918 Private
    ipaddress.ip_network("100.64.0.0/10"),      # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local / Cloud Metadata (AWS/GCP/Azure)
    ipaddress.ip_network("172.16.0.0/12"),      # RFC 1918 Private
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
    ipaddress.ip_network("192.88.99.0/24"),     # 6to4 Relay Anycast
    ipaddress.ip_network("192.168.0.0/16"),     # RFC 1918 Private
    ipaddress.ip_network("198.18.0.0/15"),      # Network benchmark tests
    ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved for future use
    ipaddress.ip_network("255.255.255.255/32"), # Broadcast
    # IPv6 blocked ranges
    ipaddress.ip_network("::/128"),             # Unspecified
    ipaddress.ip_network("::1/128"),            # Loopback
    ipaddress.ip_network("fc00::/7"),           # Unique Local Address (ULA)
    ipaddress.ip_network("fe80::/10"),          # Link-local
    ipaddress.ip_network("ff00::/8"),           # Multicast
]


def is_ip_blocked(ip_str: str) -> bool:
    """Check if an IP string belongs to any private, loopback, or reserved network."""
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved:
            return True
        for net in _BLOCKED_NETWORKS:
            if ip_obj in net:
                return True
        return False
    except ValueError:
        return True


def validate_url_security(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates a URL against SSRF rules:
      1. Scheme must be 'http' or 'https'.
      2. Hostname must be present and not 'localhost' or an IP in blocked range.
      3. DNS resolves only to public, non-reserved IP addresses.

    Returns
    -------
    (is_valid, resolved_ip, error_message)
    """
    if not url or not isinstance(url, str):
        return False, None, "URL must be a non-empty string."

    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, None, f"Invalid URL format: {e}"

    if parsed.scheme.lower() not in ("http", "https"):
        return False, None, f"Unsupported URL scheme '{parsed.scheme}'. Only 'http' and 'https' are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, None, "URL does not contain a valid hostname."

    hostname_lower = hostname.lower()
    if hostname_lower in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"):
        return False, None, f"Access to blocked hostname '{hostname}' is prohibited."

    # Pre-resolve DNS to check target IP
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
        if not addr_info:
            return False, None, f"Could not resolve DNS for host '{hostname}'."

        resolved_ips = [item[4][0] for item in addr_info]
        for ip_addr in resolved_ips:
            if is_ip_blocked(ip_addr):
                return False, ip_addr, f"Resolved IP '{ip_addr}' for host '{hostname}' is in a private or restricted network."

        return True, resolved_ips[0], None
    except socket.gaierror:
        return False, None, f"DNS resolution failed for hostname '{hostname}'."
    except Exception as e:
        return False, None, f"Security validation failed for URL '{url}': {str(e)}"
