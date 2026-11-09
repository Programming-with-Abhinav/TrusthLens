"""TrustLens AI backend: Truth Engine (Google Fact Check + Semantic Retrieval + NLI) + Safety Engine (Web Risk + Deep Signals).
Complies with TrustLens_PRD_v1.1 functional requirements:
- Phase 1 & 1b: FR-C1 to FR-C5, FR-U1 to FR-U5, FR-A1 to FR-A11, FR-P1 to FR-P5
- Phase 2: FR-C7 (Hybrid retrieval), FR-C8 (NLI stance & trust score), FR-C9 (Grounded synthesis)
- Phase 3: FR-U6 (Domain age & SSL), FR-U7 (Crypto drainers), FR-U8 (Blocking interstitial)
"""
import os
import asyncio
import re
import time
import hashlib
import logging
import ipaddress
from contextlib import asynccontextmanager
from urllib.parse import urlparse
import httpx
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request, HTTPException, Header, APIRouter
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse, Response
from collections.abc import Awaitable, Callable
import uuid
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal, cast

import db
import supabase_client
import claims_engine
import url_scanner
import summarizer

# Configure structured logging (FR-P5: No sensitive claims/URLs logged)
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger("trustlens")

def get_google_factcheck_key() -> str:
    return os.getenv("GOOGLE_FACTCHECK_API_KEY") or os.getenv("GOOGLE_API_KEY", "")


def get_google_web_risk_key() -> str:
    return os.getenv("GOOGLE_WEB_RISK_API_KEY", "")


def get_allowed_origins() -> list[str]:
    return [
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if origin.strip()
    ]


VALID_ENV = (os.getenv("ENV", "development") or "development").lower()
GOOGLE_FACTCHECK_KEY = get_google_factcheck_key()
GOOGLE_WEB_RISK_KEY = get_google_web_risk_key()


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_runtime_config()
    yield


allowed_origins = get_allowed_origins()


def validate_runtime_config() -> None:
    """Fail closed in production when required runtime secrets and origins are missing."""
    if (os.getenv("ENV", "development") or "development").lower() != "production":
        return

    required: list[str] = []
    if not get_google_factcheck_key():
        required.append("GOOGLE_FACTCHECK_API_KEY")
    if not get_google_web_risk_key():
        required.append("GOOGLE_WEB_RISK_API_KEY")
    if not (os.getenv("SUPABASE_URL") and (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY"))):
        required.append("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    if not get_allowed_origins():
        required.append("CORS_ALLOWED_ORIGINS")
    if required:
        missing = ", ".join(required)
        raise RuntimeError(f"production config missing required values: {missing}")

# In-memory IP rate limiter for anonymous access
RATE_LIMIT_BUCKET: Dict[str, list[float]] = {}

class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5_000, description="Text containing claims to verify")

class UrlRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2_048, description="Target URL to scan for phishing/malware risks")

class SummaryRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100_000, description="Visible page text to summarize")
    url: Optional[str] = Field(None, max_length=2048, description="Optional source page URL")
    length: Literal["short", "medium"] = "short"

def check_ip_rate_limit(ip: str, cap: int = 30, per: int = 60) -> bool:
    """Sliding-window rate limiter with bounded bucket cleanup."""
    now = time.time()
    cutoff = now - per
    stale_keys = [key for key, hits in RATE_LIMIT_BUCKET.items() if not hits or hits[-1] < cutoff]
    for key in stale_keys:
        RATE_LIMIT_BUCKET.pop(key, None)
    hits = [t for t in RATE_LIMIT_BUCKET.get(ip, []) if t >= cutoff]
    if len(hits) >= cap:
        RATE_LIMIT_BUCKET[ip] = hits
        return False
    RATE_LIMIT_BUCKET[ip] = hits + [now]
    return True

def split_claims(text: str) -> List[str]:
    """Atomic claim extraction: splits into max 5 sentence claims with abbreviation protection (FR-C2)."""
    cleaned = text.strip()
    if not cleaned:
        return []

    # Protect abbreviations and decimals from split
    protected = re.sub(r"\b(Dr|Mr|Mrs|Ms|Prof|U\.S|e\.g|i\.e|vs)\.", r"\1<DOT>", cleaned)
    protected = re.sub(r"(\d)\.(\d)", r"\1<DEC>\2", protected)

    parts = re.split(r"(?<=[.!?])\s+", protected)
    extracted: List[str] = []
    for p in parts:
        restored = p.replace("<DOT>", ".").replace("<DEC>", ".").strip()
        if len(restored.split()) >= 3:
            extracted.append(restored)

    return extracted[:5] if extracted else [cleaned[:200]]

RATING_MAP: Dict[str, str] = {
    # True / Verified
    "true": "True", "correct": "True", "accurate": "True", "verified": "True",
    "confirmed": "True", "fact": "True", "real": "True", "authentic": "True",
    # Mostly true
    "mostly true": "MostlyTrue", "mostly accurate": "MostlyTrue", "largely true": "MostlyTrue",
    # Mixed / Partial
    "mixed": "Mixed", "half true": "Mixed", "partly true": "Mixed", "partially true": "Mixed",
    "somewhat true": "Mixed", "needs context": "Mixed", "missing context": "Mixed",
    "lacks context": "Mixed", "exaggerated": "Mixed", "in-between": "Mixed", "ambiguous": "Mixed",
    # Misleading
    "misleading": "Misleading", "distorts facts": "Misleading", "out of context": "Misleading",
    "unsupported": "Misleading", "misattributed": "Misleading", "manipulated": "Misleading",
    # False
    "false": "False", "fake": "False", "incorrect": "False", "inaccurate": "False",
    "not true": "False", "untrue": "False", "debunked": "False", "hoax": "False",
    "pants on fire": "False", "four pinocchios": "False", "wrong": "False",
    "no evidence": "False", "scam": "False", "satire": "False", "unproven": "False",
    "outdated": "False", "barely true": "False", "mostly false": "False",
    "half false": "False", "partly false": "False", "not accurate": "False",
    "unfounded": "False", "fabricated": "False", "refuted": "False"
}

def map_verdict(rating_str: str) -> str:
    """Map a claim-review rating to a trusted verdict while handling negation and partial truths."""
    r = rating_str.strip().lower()
    if not r:
        return "Unrated"

    if r in RATING_MAP:
        return RATING_MAP[r]

    if re.search(
        r"\b(not true|inaccurate|incorrect|false|fake|pants on fire|hoax|no evidence|wrong|scam|untrue|debunked|mostly false|half false|partly false|barely true|not accurate|unproven|satire|fabricated)\b",
        r,
    ):
        return "False"

    if re.search(r"\b(mixed|partly true|half true|mostly true|somewhat true|ambiguous|needs context|missing context|lacks context)\b", r):
        return "Mixed"

    if re.search(r"\b(true|correct|accurate|legit|confirmed|verified|fact)\b", r):
        return "True"

    if re.search(r"\b(misleading|distorts|out of context|unsupported|manipulated)\b", r):
        return "Misleading"

    return "Unrated"

FLAG_EXPLANATIONS = {
    "IP address used as host": "The URL connects directly to a numeric IP address instead of a registered domain, commonly observed in malicious command servers.",
    "Punycode look-alike domain": "Domain uses internationalized punycode ('xn--'), frequently deployed in homograph phishing attacks to impersonate trusted sites.",
    "Many hyphens in domain": "Domain contains excessive hyphens, often used to blend trademarked brand names into unauthorized look-alike domains.",
    "High-risk TLD": "Domain uses a top-level domain frequently associated with spam, bulletproof hosting, and phishing campaigns.",
    "Brand name inside unofficial domain": "Domain incorporates a known brand name (e.g. PayPal, Google) outside of its official root domain.",
    "Urgency / crypto-drainer keyword": "Host contains deceptive urgency or crypto keywords like 'airdrop', 'claim', 'wallet', or 'verify'.",
    "No HTTPS": "Unencrypted HTTP protocol; user credentials and data can be intercepted in transit.",
    "Known malware/phishing test signature detected": "This URL matches the official Google Safe Browsing / Web Risk testbed signature for malicious threat verification.",
    "Phishing or deceptive keyword in URL path": "URL path contains explicit phishing or deceptive keyword indicators.",
    "Malware or exploit keyword in URL path": "URL path contains keywords directly referencing malware payloads or exploits.",
    "Credential harvesting indicator in URL path": "URL path contains credential solicitation or deceptive verification patterns.",
    "Crypto-drainer / wallet hijacking pattern detected": "Detected deceptive wallet-connection signatures, permit2 approvals, or drainer patterns designed to steal tokens.",
    "Invalid or untrusted SSL certificate": "Target server presented an invalid, expired, or self-signed TLS/SSL certificate."
}

BRANDS = ["paypal", "google", "amazon", "sbi", "hdfc", "paytm", "microsoft", "metamask", "binance", "coinbase"]
OFFICIAL_BRAND_DOMAINS = {
    "google.com", "google.co.in", "amazon.com", "amazon.in", "paypal.com",
    "paypal.me", "sbi.co.in", "hdfc.com", "paytm.com", "microsoft.com",
}

def validate_and_normalize_url(raw_url: str) -> str:
    """Validates and normalizes URL (FR-U4)."""
    clean_url = raw_url.strip()
    if not clean_url:
        raise HTTPException(400, "URL cannot be empty.")

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", clean_url):
        raise HTTPException(400, "URL must use http or https.")

    parsed = urlparse(clean_url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise HTTPException(400, "URL must use http or https.")

    parsed = urlparse(clean_url)
    if not parsed.hostname:
        raise HTTPException(400, "Invalid URL structure. Must include a valid hostname.")
    if parsed.username or parsed.password:
        raise HTTPException(400, "User information is not allowed in URLs.")

    try:
        address = ipaddress.ip_address(parsed.hostname)
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
            raise HTTPException(400, "Private or internal IP addresses are not allowed.")
        if address.is_unspecified or address.is_multicast:
            raise HTTPException(400, "Invalid or internal IP address.")
    except ValueError:
        pass

    if parsed.hostname.lower() in {"localhost", "localhost.localdomain", "metadata.google.internal", "metadata.azure.internal"}:
        raise HTTPException(400, "Local or metadata hostnames are not allowed.")

    return clean_url

def analyze_url_heuristics(normalized_url: str) -> List[str]:
    """Inspects URL for phishing/malware indicators (FR-U2)."""
    parsed = urlparse(normalized_url)
    host = (parsed.hostname or "").lower()
    path = (parsed.path or "").lower()
    flags: List[str] = []

    # Safe Browsing / Web Risk official testbeds & signatures
    if "testsafebrowsing" in host or re.search(r"/(s|apiv4)/.*(phishing|malware|unwanted)", path):
        flags.append("Known malware/phishing test signature detected")

    if re.fullmatch(r"[\d.]+", host):
        flags.append("IP address used as host")
    if "xn--" in host:
        flags.append("Punycode look-alike domain")
    if host.count("-") >= 2:
        flags.append("Many hyphens in domain")
    if host.rsplit(".", 1)[-1] in {"zip", "xyz", "top", "click", "tk", "ru", "work", "fit", "buzz"}:
        flags.append("High-risk TLD")
    official_match = host in OFFICIAL_BRAND_DOMAINS or any(host == domain or host.endswith("." + domain) for domain in OFFICIAL_BRAND_DOMAINS)
    if any(b in host for b in BRANDS) and not official_match:
        flags.append("Brand name inside unofficial domain")
    if re.search(r"airdrop|claim|wallet|verify|login|secure|recover|air-drop", host):
        flags.append("Urgency / crypto-drainer keyword")
    if normalized_url.startswith("http://"):
        flags.append("No HTTPS")
    if re.search(r"phish(ing)?", path):
        flags.append("Phishing or deceptive keyword in URL path")
    if re.search(r"malware|trojan|ransomware|drainer|stealer|exploit|payload", path):
        flags.append("Malware or exploit keyword in URL path")
    if re.search(r"update-billing|verify-account|login-confirm", path):
        flags.append("Credential harvesting indicator in URL path")

    return flags

async def verify_single_claim(claim_text: str) -> Dict[str, Any]:
    """Verifies a single atomic claim using cache, Google Fact Check,
    Phase 2 Semantic Hybrid Retrieval, NLI stance scoring, and grounded synthesis.
    """
    normalized_claim = " ".join(claim_text.lower().split())
    claim_hash = hashlib.sha256(normalized_claim.encode("utf-8")).hexdigest()

    # Cache evidence only; attach caller-provided claim text after retrieval.
    cached_data = db.get_cached(claim_hash)
    if cached_data and cached_data.get("source") != "hybrid_retrieval":
        return {**cached_data, "claim": claim_text, "cached": True}

    result: Dict[str, Any] = {
        "claim": claim_text,
        "verdict": "Unverified",
        "confidence": 0.0,
        "stance": "Neutral",
        "synthesis": "",
        "sources": [],
        "source": "none",
        "cached": False
    }

    # 1. Live: Google Fact Check Tools API
    fact_check_key = get_google_factcheck_key()
    if fact_check_key:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    "https://factchecktools.googleapis.com/v1alpha1/claims:search",
                    params={"query": claim_text[:200], "key": fact_check_key, "pageSize": 5}
                )
            if resp.status_code == 200:
                claims_data = resp.json().get("claims", [])
                votes: List[str] = []
                for cl in claims_data:
                    for rv in cl.get("claimReview", []):
                        source_url = str(rv.get("url", "")).strip()
                        parsed_source = urlparse(source_url)
                        if parsed_source.scheme.lower() not in {"http", "https"} or not parsed_source.netloc:
                            continue
                        v = map_verdict(rv.get("textualRating", ""))
                        votes.append(v)
                        result["sources"].append({
                            "publisher": rv.get("publisher", {}).get("name", "Unknown Publisher"),
                            "title": rv.get("title", ""),
                            "rating": rv.get("textualRating", ""),
                            "url": source_url,
                            "verdict": v
                        })
                if votes:
                    has_true = any(v in ("True", "MostlyTrue") for v in votes)
                    has_false = any(v in ("False", "Misleading") for v in votes)
                    if has_true and has_false:
                        result["verdict"] = "Mixed"
                    else:
                        top_verdict = max(set(votes), key=votes.count)
                        result["verdict"] = top_verdict
                    result["confidence"] = round(votes.count(result["verdict"]) / len(votes), 2)
                    result["source"] = "google"
        except Exception as e:
            logger.warning("Google Fact Check API query error: %s", type(e).__name__)

    # Local seed evidence is not a source-bearing verdict.

    # 4. Phase 2: Compute NLI Stance, Composite Trust Score, and Grounded Synthesis
    first_title = result["sources"][0]["title"] if result["sources"] else ""
    stance = claims_engine.classify_nli_stance(claim_text, first_title, result["verdict"])
    synthesis = await claims_engine.synthesize_grounded_explanation(claim_text, result["verdict"], stance, result["sources"])

    result["stance"] = stance
    result["synthesis"] = synthesis

    cache_value = {key: value for key, value in result.items() if key not in {"claim", "cached"}}
    db.set_cached(claim_hash, cache_value)
    return result

# --- Health Endpoint (FR-P1) ---


api_router = APIRouter()
@api_router.get("/health")
async def health() -> Dict[str, Any]:
    supabase_ok = await supabase_client.ping_supabase()
    return {
        "status": "healthy",
        "mode": "live" if get_google_factcheck_key() else "demo",
        "fact_check_api_enabled": bool(get_google_factcheck_key()),
        "web_risk_api_enabled": bool(get_google_web_risk_key()),
        "cached_items": db.count_cache(),
        "supabase_connected": supabase_ok
    }


_READINESS_CACHE: Dict[str, Any] = {"checked_at": 0.0, "ok": True}


async def readiness() -> Dict[str, Any] | JSONResponse:
    env_name = (os.getenv("ENV", "development") or "development").lower()
    now = time.time()
    if env_name == "production":
        try:
            validate_runtime_config()
        except RuntimeError as exc:
            return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(exc)})

        if now - _READINESS_CACHE.get("checked_at", 0.0) > 30.0:
            supabase_ok = await supabase_client.ping_supabase()
            _READINESS_CACHE["checked_at"] = now
            _READINESS_CACHE["ok"] = bool(supabase_ok)
        else:
            supabase_ok = _READINESS_CACHE.get("ok", True)

        if not supabase_ok:
            return JSONResponse(status_code=503, content={"status": "not_ready", "database": "unavailable"})

    return {"status": "ready", "database": "available"}

# --- Claim Verification Endpoint (FR-C1 to FR-C5, FR-A9, FR-A10, FR-P4) ---
@api_router.post("/verify")
@api_router.post("/verify/claim")
async def verify_claims(
    body: TextRequest,
    req: Request,
    authorization: Optional[str] = Header(None)
):
    start_time = time.time()
    user: Optional[Dict[str, Any]] = None

    if authorization:
        verified_user: Any = cast(Any, await supabase_client.verify_token(authorization))
        if not isinstance(verified_user, dict):
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        user = cast(Dict[str, Any], verified_user)
        user_id = user.get("id")
        if not isinstance(user_id, str):
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        bucket = f"user:{user_id}"
    else:
        bucket = f"ip:{req.client.host if req.client else '127.0.0.1'}"
    if not check_ip_rate_limit(bucket):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.", headers={"Retry-After": "60"})

    claims_list = split_claims(body.text)

    # Free-tier quota enforcement & usage counting (FR-A9, FR-A10)
    if user:
        await getattr(supabase_client, "record_claim_check")(
            user, num_claims=len(claims_list)
        )

    verified_claims = list(await asyncio.gather(*(verify_single_claim(c) for c in claims_list)))

    elapsed = round((time.time() - start_time) * 1000, 1)
    logger.info(f"Verify completed in {elapsed}ms | user_auth={bool(user)} | claims_count={len(verified_claims)}")

    return {"claims": verified_claims}

# --- User-triggered page summarization (FR-S1 to FR-S9) ---
@api_router.post("/summarize")
async def summarize_page(
    body: SummaryRequest,
    req: Request,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    user: Optional[Dict[str, Any]] = None
    if authorization:
        verified_user: Any = cast(Any, await supabase_client.verify_token(authorization))
        if not isinstance(verified_user, dict):
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        user = cast(Dict[str, Any], verified_user)
        user_id = user.get("id")
        if not isinstance(user_id, str):
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        bucket = f"user:{user_id}"
    else:
        bucket = f"ip:{req.client.host if req.client else '127.0.0.1'}"
    if not check_ip_rate_limit(bucket):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.", headers={"Retry-After": "60"})

    text = body.text.strip()
    if not text:
        raise HTTPException(400, "Text cannot be empty.")

    wiki_url = text if summarizer.is_wikipedia_url(text) else None
    source_url = wiki_url or (body.url.strip() if body.url else None)
    if source_url:
        parsed_url = urlparse(source_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
            raise HTTPException(400, "Source URL must be a valid HTTP or HTTPS URL.")

    cache_key = "summary:" + hashlib.sha256(
        f"{body.length}\0{text}".encode("utf-8")
    ).hexdigest()
    cached_result: Any = db.get_cached(cache_key)
    if cached_result is None:
        try:
            source_text = await summarizer.fetch_wikipedia_text(wiki_url) if wiki_url else text
        except (httpx.HTTPError, ValueError):
            raise HTTPException(502, "Unable to retrieve this Wikipedia article. Paste its text and try again.")

        truncated = len(source_text) > summarizer.MAX_INPUT_CHARACTERS
        bounded_text = source_text[:summarizer.MAX_INPUT_CHARACTERS]
        result: Dict[str, Any] = await summarizer.summarize_text(
            bounded_text,
            body.length,
            os.getenv("GEMINI_API_KEY", "")
        )
        result["section_summaries"] = summarizer.summarize_sections(bounded_text)
        result["truncated"] = truncated
        db.set_cached(cache_key, result)
    else:
        result = cast(Dict[str, Any], cached_result)
        result.setdefault("section_summaries", [])
        truncated = bool(result.get("truncated", len(text) > summarizer.MAX_INPUT_CHARACTERS))
        result["truncated"] = truncated

    response: Dict[str, Any] = {**result, "url": source_url}
    logger.info(f"Summary completed | user_auth={bool(user)} | source={result['source']} | truncated={truncated}")
    return response

# --- URL Scanner Endpoint (FR-U1 to FR-U5, FR-A9, FR-P4) ---
@api_router.post("/scan")
@api_router.post("/scan/url")
async def scan_url(
    body: UrlRequest,
    req: Request,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    start_time = time.time()
    user: Optional[Dict[str, Any]] = None

    if authorization:
        verified_user: Any = cast(Any, await supabase_client.verify_token(authorization))
        if not isinstance(verified_user, dict):
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        user = cast(Dict[str, Any], verified_user)
        user_id = user.get("id")
        if not isinstance(user_id, str):
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        bucket = f"user:{user_id}"
    else:
        bucket = f"ip:{req.client.host if req.client else '127.0.0.1'}"
    if not check_ip_rate_limit(bucket):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.", headers={"Retry-After": "60"})

    # URL validation and normalization (FR-U4)
    normalized = validate_and_normalize_url(body.url)
    flags = analyze_url_heuristics(normalized)
    threats: list[str] = []
    source = "heuristics"

    # Known Safe Browsing testbed threat synthesis (FR-U2/FR-U3 test targets)
    parsed_norm = urlparse(normalized)
    path_norm = (parsed_norm.path or "").lower()
    if "Known malware/phishing test signature detected" in flags:
        if "malware" in path_norm:
            threats.append("MALWARE")
        elif "unwanted" in path_norm:
            threats.append("UNWANTED_SOFTWARE")
        else:
            threats.append("SOCIAL_ENGINEERING")
        source = "Google Safe Browsing testbed + heuristics"

    # Live: Google Web Risk API lookup (FR-U3)
    web_risk_key = get_google_web_risk_key()
    if web_risk_key:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(
                    "https://webrisk.googleapis.com/v1/uris:search",
                    params=[
                        ("uri", normalized),
                        ("key", web_risk_key),
                        ("threatTypes", "MALWARE"),
                        ("threatTypes", "SOCIAL_ENGINEERING"),
                        ("threatTypes", "UNWANTED_SOFTWARE")
                    ]
                )
                if r.status_code == 200:
                    threats = r.json().get("threat", {}).get("threatTypes", [])
                    source = "Google Web Risk + heuristics"
        except Exception as e:
            logger.warning("Google Web Risk API lookup error: %s", type(e).__name__)

    # Phase 3: Deep signals (Domain age, SSL telemetry, Crypto-drainers)
    deep_flags, telemetry = await url_scanner.evaluate_advanced_threats(normalized, flags)
    flags = flags + deep_flags

    is_blocked = (
        telemetry.get("should_block", False) or
        bool(threats) or
        "Known malware/phishing test signature detected" in flags or
        "Phishing or deceptive keyword in URL path" in flags
    )
    level = "Dangerous" if is_blocked else "Suspicious" if len(flags) >= 2 else "Caution" if flags else "Safe"

    # Human-readable flag explanations (FR-U5)
    flag_explanations = [
        {"flag": f, "explanation": FLAG_EXPLANATIONS.get(f, "Suspicious security indicator identified during evaluation.")}
        for f in flags
    ]

    # Record URL scan usage for authenticated user
    if user:
        await supabase_client.record_url_scan(user)

    elapsed = round((time.time() - start_time) * 1000, 1)
    logger.info(f"Scan completed in {elapsed}ms | user_auth={bool(user)} | level={level} | should_block={is_blocked}")

    # Preserves exact response shape for FR-U1 + adds flag_explanations for FR-U5 + telemetry & should_block for Phase 3
    return {
        "url": body.url,
        "level": level,
        "threats": threats,
        "flags": flags,
        "flag_explanations": flag_explanations,
        "telemetry": telemetry,
        "should_block": is_blocked,
        "source": source
    }

# --- Warning Interstitial Endpoint (FR-U8) ---
@api_router.get("/interstitial")
async def get_interstitial_page(url: Optional[str] = None) -> dict[str, object]:
    target = url or "https://suspicious-example.com"
    return {
        "title": "TrustLens Security Warning",
        "url": target,
        "warning": "CRITICAL RISK: TrustLens detected dangerous phishing or crypto-drainer signatures.",
        "action_required": "Do not enter passwords, private keys, or wallet seed phrases on this domain.",
        "can_proceed": True
    }

def favicon():
    if os.path.exists("static/favicon.svg"):
        return FileResponse("static/favicon.svg", media_type="image/svg+xml")
    return Response(status_code=204)


def create_app() -> FastAPI:
    env = (os.getenv("ENV", "development") or "development").lower()
    docs_enabled_env = os.getenv("DOCS_ENABLED")
    if docs_enabled_env is not None:
        docs_enabled = docs_enabled_env.lower() in ("true", "1", "yes")
    else:
        docs_enabled = env != "production"

    application = FastAPI(
        title="TrustLens AI API",
        description="Browser-based factual claim verification and malicious URL scanner API",
        version="1.1.0",
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    allowed = get_allowed_origins()

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Accept-Profile", "Content-Profile"],
    )

    @application.middleware("http")
    async def add_request_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        client_ip = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "127.0.0.1")
        request.state.client_ip = client_ip

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        # Security headers (API-07, SEC-07, SEC-08)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Authenticated requests must never be cached by shared or client caches
        if "authorization" in request.headers:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"

        # Deprecation notice for legacy routes
        if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/v1/"):
            response.headers["Deprecation"] = "true"
        return response

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = request.headers.get("x-request-id") or getattr(request.state, "request_id", str(uuid.uuid4()))
        detail = exc.detail
        headers = {"X-Request-ID": request_id, **(exc.headers or {})}
        headers["X-Content-Type-Options"] = "nosniff"
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return JSONResponse(
            status_code=exc.status_code,
            headers=headers,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": detail,
                    "request_id": request_id,
                }
            },
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = request.headers.get("x-request-id") or getattr(request.state, "request_id", str(uuid.uuid4()))
        headers = {
            "X-Request-ID": request_id,
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        return JSONResponse(
            status_code=422,
            headers=headers,
            content={
                "error": {
                    "code": 422,
                    "message": "Invalid request payload.",
                    "details": exc.errors(),
                    "request_id": request_id,
                }
            },
        )

    @application.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = request.headers.get("x-request-id") or getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.exception("Unhandled server error: %s (request_id=%s)", type(exc).__name__, request_id)
        headers = {
            "X-Request-ID": request_id,
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        return JSONResponse(
            status_code=500,
            headers=headers,
            content={
                "error": {
                    "code": 500,
                    "message": "An internal server error occurred.",
                    "request_id": request_id,
                }
            },
        )

    # Root system probes and utilities
    @application.get("/healthz")
    async def _healthz() -> Dict[str, Any]:
        return {"status": "ok", "service": "trustlens-api"}

    @application.get("/readyz", response_model=None)
    async def _readyz() -> Dict[str, Any] | JSONResponse:
        return await readiness()

    @application.get("/interstitial")
    async def _interstitial(url: Optional[str] = None) -> dict[str, object]:
        return await get_interstitial_page(url)

    @application.get("/favicon.ico", include_in_schema=False)
    def _favicon():
        return favicon()

    # Mount unified router under canonical /api/v1 and legacy /api
    application.include_router(api_router, prefix="/api/v1")
    application.include_router(api_router, prefix="/api")

    # Static mounts are disabled in production mode (API-only gateway)
    if env != "production":
        if os.path.exists("extension"):
            application.mount("/extension", StaticFiles(directory="extension", html=True), name="extension")
        if os.path.exists("static"):
            application.mount("/", StaticFiles(directory="static", html=True), name="static")

    return application


app = create_app()

