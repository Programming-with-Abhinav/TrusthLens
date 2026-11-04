"""TrustLens AI - Advanced URL & Threat Defense Engine (Phase 3).
Implements:
- FR-U6: Deep Domain Age (RDAP / WHOIS) and Live SSL Certificate Telemetry
- FR-U7: Web3 & Crypto-Drainer Script and Pattern Detection
- FR-U8: Threat Scoring & Interstitial Triggers
"""
import ssl
import socket
import datetime
from urllib.parse import urlparse
import re
from typing import Dict, Any, List, Optional, Tuple
import httpx

RDAP_CACHE: Dict[str, Dict[str, Any]] = {}
SSL_CACHE: Dict[str, Dict[str, Any]] = {}

# Known crypto-drainer & wallet theft indicators (FR-U7)
CRYPTO_DRAINER_PATTERNS = [
    r"seaport.*order",
    r"permit2",
    r"setapprovalforall",
    r"claim.*airdrop",
    r"airdrop.*claim",
    r"connect.*wallet.*reward",
    r"drainer",
    r"wallet.*verify.*seed",
    r"keystore.*restore",
    r"metamask.*security.*update",
    r"phantom.*airdrop",
    r"binance.*gift",
    r"revoke.*cash.*approve"
]

async def lookup_domain_age(domain: str) -> Optional[int]:
    """Queries RDAP to determine domain registration age in days (FR-U6).
    Returns age in days or None if lookup unavailable.
    """
    clean_domain = domain.lower().split(":")[0]
    if not clean_domain or clean_domain in ("localhost", "127.0.0.1") or re.match(r"^[\d.]+$", clean_domain):
        return None

    # Check memory cache
    if clean_domain in RDAP_CACHE:
        return RDAP_CACHE[clean_domain].get("age_days")

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"https://rdap.org/domain/{clean_domain}", follow_redirects=True)
            if resp.status_code == 200:
                data = resp.json()
                events = data.get("events", [])
                reg_date_str = None
                for ev in events:
                    if ev.get("eventAction") in ("registration", "registered", "created"):
                        reg_date_str = ev.get("eventDate")
                        break
                if reg_date_str:
                    reg_dt = datetime.datetime.fromisoformat(reg_date_str.replace("Z", "+00:00"))
                    now = datetime.datetime.now(datetime.timezone.utc)
                    age_days = (now - reg_dt).days
                    RDAP_CACHE[clean_domain] = {"age_days": age_days}
                    return age_days
    except Exception:
        pass
    return None

def check_ssl_certificate(hostname: str, port: int = 443) -> Dict[str, Any]:
    """Inspects live SSL/TLS certificate entropy, validity, and issuer (FR-U6)."""
    clean_host = hostname.lower().split(":")[0]
    if not clean_host or clean_host in ("localhost", "127.0.0.1") or re.match(r"^[\d.]+$", clean_host):
        return {"valid": False, "issuer": "None", "days_until_expiry": 0, "error": "Direct IP / local host"}

    if clean_host in SSL_CACHE:
        return SSL_CACHE[clean_host]

    ctx = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED

    try:
        with socket.create_connection((clean_host, port), timeout=3.0) as sock:
            with ctx.wrap_socket(sock, server_hostname=clean_host) as ssock:
                cert = ssock.getpeercert()
                if not cert:
                    return {"valid": False, "issuer": "Unknown", "days_until_expiry": 0}

                # Parse issuer
                issuer_dict = dict(x[0] for x in cert.get("issuer", []))
                issuer_name = issuer_dict.get("organizationName") or issuer_dict.get("commonName") or "Unknown"

                # Parse expiry
                not_after = cert.get("notAfter")
                expiry_dt = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=datetime.timezone.utc)
                days_left = (expiry_dt - datetime.datetime.now(datetime.timezone.utc)).days

                result = {
                    "valid": True,
                    "issuer": issuer_name,
                    "days_until_expiry": max(days_left, 0)
                }
                SSL_CACHE[clean_host] = result
                return result
    except ssl.SSLCertVerificationError as e:
        return {"valid": False, "issuer": "Untrusted / Self-signed", "days_until_expiry": 0, "error": str(e)}
    except Exception as e:
        return {"valid": False, "issuer": "Connection error", "days_until_expiry": 0, "error": str(e)}

def analyze_crypto_drainers(url: str) -> List[str]:
    """Detects crypto-drainer signatures, deceptive airdrops, and permit2 hijacking (FR-U7)."""
    flags = []
    url_lower = url.lower()
    for pattern in CRYPTO_DRAINER_PATTERNS:
        if re.search(pattern, url_lower):
            flags.append("Crypto-drainer / wallet hijacking pattern detected")
            break

    # Look for deceptive wallet connect subdomains
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if re.search(r"connect-wallet|claim-nft|airdrop-eth|uniswap-v4-claim", host):
        if "Crypto-drainer / wallet hijacking pattern detected" not in flags:
            flags.append("Crypto-drainer / wallet hijacking pattern detected")
    return flags

async def evaluate_advanced_threats(normalized_url: str, base_flags: List[str]) -> Tuple[List[str], Dict[str, Any]]:
    """Evaluates Phase 3 deep signals: Domain Age, SSL Telemetry, and Crypto-Drainers."""
    parsed = urlparse(normalized_url)
    host = parsed.hostname or ""
    additional_flags = []
    telemetry = {
        "domain_age_days": None,
        "ssl": None,
        "should_block": False
    }

    # 1. Domain age check
    age_days = await lookup_domain_age(host)
    if age_days is not None:
        telemetry["domain_age_days"] = age_days
        if age_days < 30:
            additional_flags.append(f"Zero-day domain: Registered only {age_days} days ago (< 30 days)")

    # 2. SSL certificate check if HTTPS
    if normalized_url.startswith("https://"):
        ssl_info = check_ssl_certificate(host)
        telemetry["ssl"] = ssl_info
        if not ssl_info.get("valid") and "Untrusted" in ssl_info.get("issuer", ""):
            additional_flags.append("Invalid or untrusted SSL certificate")

    # 3. Crypto drainer heuristics
    drainer_flags = analyze_crypto_drainers(normalized_url)
    additional_flags.extend(drainer_flags)

    # 4. Critical block decision (FR-U8 Interstitial trigger)
    all_combined = base_flags + additional_flags
    has_brand = any("Brand name inside unofficial" in f for f in all_combined)
    has_zero_day = any("Zero-day" in f for f in all_combined)
    is_critical_risk = (
        any("Punycode" in f for f in all_combined) or
        any("Crypto-drainer" in f for f in all_combined) or
        any("Known malware/phishing test signature" in f for f in all_combined) or
        any("Phishing" in f for f in all_combined) or
        (has_brand and has_zero_day)
    )
    telemetry["should_block"] = is_critical_risk

    return additional_flags, telemetry
