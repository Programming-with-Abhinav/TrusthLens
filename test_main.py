"""Test suite for TrustLens AI FastAPI backend.
Validates all requirements specified in TrustLens_PRD_v1.1.
"""
from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from pytest import MonkeyPatch, fixture
import main
import summarizer

client: Any = TestClient(main.app)


@fixture(autouse=True)
def reset_rate_limits():
    main.RATE_LIMIT_BUCKET.clear()
    yield
    main.RATE_LIMIT_BUCKET.clear()

def test_health():
    resp: Response = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["mode"] in ("live", "demo")

def test_health_versioned():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200


def test_production_requires_runtime_config(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://app.trustlens.ai")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.delenv("GOOGLE_FACTCHECK_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_WEB_RISK_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="production.*config"):
        main.validate_runtime_config()


def test_liveness_readiness_and_request_id():
    live = client.get("/healthz")
    ready = client.get("/readyz")
    explicit = client.get("/healthz", headers={"X-Request-ID": "req-phase8"})

    assert live.status_code == 200
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    assert explicit.headers["X-Request-ID"] == "req-phase8"


def test_uniform_http_error_json_and_request_id():
    resp = client.post("/api/scan", json={"url": "javascript:alert(1)"}, headers={"X-Request-ID": "req-error"})

    assert resp.status_code == 400
    assert resp.headers["X-Request-ID"] == "req-error"
    assert resp.json()["error"]["request_id"] == "req-error"
    assert "message" in resp.json()["error"]

def test_scan_flags_lookalike():
    resp = client.post("/api/scan", json={"url": "http://paypal-secure-login.xyz/claim"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["level"] in ("Suspicious", "Dangerous")
    assert any("Brand name" in f for f in data["flags"])
    assert "flag_explanations" in data


def test_scan_official_brand_domains_are_not_brand_flags():
    for url in ("https://google.co.in", "https://amazon.in", "https://paypal.me", "https://sbi.co.in"):
        resp = client.post("/api/scan", json={"url": url})
        assert resp.status_code == 200
        assert not any("Brand name" in flag for flag in resp.json()["flags"])

def test_scan_invalid_url_rejected():
    # FR-U4: reject malformed input with a clear error
    resp = client.post("/api/scan", json={"url": "not-a-valid-url-without-host"})
    assert resp.status_code == 400


def test_scan_rejects_non_http_scheme():
    for url in ("javascript:alert(1)", "file:///etc/passwd", "ftp://example.com/file"):
        resp = client.post("/api/scan", json={"url": url})
        assert resp.status_code == 400


def test_scan_rejects_ssrf_targets():
    for url in (
        "http://127.0.0.1/admin",
        "http://10.0.0.1/admin",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/admin",
        "http://user:pass@example.com/login",
        "http://localhost/admin",
    ):
        resp = client.post("/api/scan", json={"url": url})
        assert resp.status_code == 400

def test_scan_does_not_call_web_risk_without_separate_key(monkeypatch: MonkeyPatch):
    monkeypatch.setattr(main, "GOOGLE_WEB_RISK_KEY", "")

    class UnexpectedAsyncClient:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise AssertionError("Web Risk must not be called without its separate key")

    monkeypatch.setattr(main.httpx, "AsyncClient", UnexpectedAsyncClient)
    resp = client.post("/api/scan", json={"url": "https://example.com"})

    assert resp.status_code == 200
    assert resp.json()["source"] == "heuristics"

def test_verify_returns_claims():
    resp = client.post("/api/verify", json={"text": "5G towers spread respiratory viruses quickly."})
    assert resp.status_code == 200
    data = resp.json()
    assert "claims" in data
    assert len(data["claims"]) >= 1
    # FR-C4: source field present
    assert "source" in data["claims"][0]

def test_verify_max_five_claims_cap():
    # FR-C2: Split input into at most 5 sentence-like claims
    long_text = ". ".join([f"This is claim number {i} with several words included" for i in range(10)]) + "."
    resp = client.post("/api/verify", json={"text": long_text})
    assert resp.status_code == 200
    assert len(resp.json()["claims"]) <= 5

def test_verify_no_evidence_found():
    # FR-C5: Return "no evidence found" explicitly rather than a guessed verdict
    resp = client.post("/api/verify", json={"text": "Some completely unheard random statement xyz123."})
    assert resp.status_code == 200
    claims = resp.json()["claims"]
    assert claims[0]["verdict"] == "Unverified"


def test_map_verdict_handles_negation_and_unknown_ratings():
    assert main.map_verdict("Partly true") == "Mixed"
    assert main.map_verdict("Not true") == "False"
    assert main.map_verdict("Inaccurate") == "False"
    assert main.map_verdict("Unrecognized rating text") == "Unrated"


def test_demo_database_is_removed():
    assert not hasattr(main, "DEMO_DATABASE")


def test_verification_cache_excludes_claim_text(monkeypatch: MonkeyPatch):
    cache: dict[str, dict[str, Any]] = {}
    marker = "MARKER-7f3a"
    monkeypatch.setattr(main.db, "get_cached", lambda key: cache.get(key))
    monkeypatch.setattr(main.db, "set_cached", lambda key, value: cache.__setitem__(key, value))
    monkeypatch.setattr(main, "GOOGLE_FACTCHECK_KEY", "")

    resp = client.post("/api/verify", json={"text": marker})

    assert resp.status_code == 200
    assert marker not in repr(cache)

def test_summarize_uses_extracts_from_supplied_text(monkeypatch: MonkeyPatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    text = (
        "The city opened a new public library downtown. The library offers free internet access. "
        "Residents can borrow books and attend weekly science workshops."
    )
    resp = client.post("/api/summarize", json={"text": text, "length": "short"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "extractive"
    assert data["truncated"] is False
    assert 1 <= len(data["key_points"]) <= 3
    assert all(point in text for point in data["key_points"])
    assert all(point in text for point in data["summary"].split(". ") if point)

def test_summarize_reports_truncated_long_input(monkeypatch: MonkeyPatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    text = ("A long report describes the annual community science research program. " * 900)
    resp = client.post("/api/summarize", json={"text": text, "length": "medium"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["truncated"] is True
    assert data["source"] == "extractive"
    assert 1 <= len(data["key_points"]) <= 5

def test_summarize_validates_empty_text_and_source_url():
    empty = client.post("/api/summarize", json={"text": "   "})
    invalid_url = client.post(
        "/api/summarize",
        json={"text": "A useful article has several clear sentences.", "url": "javascript:alert(1)"}
    )

    assert empty.status_code == 400
    assert invalid_url.status_code == 400

def test_summarize_cache_uses_hash_without_storing_input(monkeypatch: MonkeyPatch):
    cache: dict[str, dict[str, Any]] = {}
    calls = 0
    text = "Private cache check unique sentence. Another sentence makes this a page."

    async def fake_summarize(source_text: str, length: str, gemini_key: str = "") -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return {"summary": "A source-based summary.", "key_points": ["A source-based summary."], "source": "extractive"}

    def get_cached(key: str) -> dict[str, Any] | None:
        return cache.get(key)

    def set_cached(key: str, value: dict[str, Any]) -> None:
        cache[key] = value

    monkeypatch.setattr(main.db, "get_cached", get_cached)
    monkeypatch.setattr(main.db, "set_cached", set_cached)
    monkeypatch.setattr(main.summarizer, "summarize_text", fake_summarize)

    first = client.post("/api/summarize", json={"text": text})
    second = client.post("/api/summarize", json={"text": text})

    assert first.status_code == second.status_code == 200
    assert calls == 1
    assert text not in repr(cache)

def test_summarizer_chunks_long_documents():
    text = " ".join(f"Section {index} explains a different research finding." for index in range(600))
    chunks = summarizer.chunk_sentences(summarizer.split_sentences(text))

    assert len(chunks) > 1
    assert all(len(" ".join(chunk)) <= summarizer.CHUNK_CHARACTERS for chunk in chunks)

def test_wikipedia_urls_are_restricted_to_wikipedia_hosts():
    assert summarizer.is_wikipedia_url("https://en.wikipedia.org/wiki/TrustLens")
    assert not summarizer.is_wikipedia_url("https://wikipedia.org.attacker.example/wiki/TrustLens")
    assert not summarizer.is_wikipedia_url("http://en.wikipedia.org/wiki/TrustLens")

def test_summarize_wikipedia_link_returns_section_summaries(monkeypatch: MonkeyPatch):
    wiki_url = "https://en.wikipedia.org/wiki/TrustLens_Test_Article"
    article = (
        "Opening overview of this research project.\n"
        "== History ==\nThe project began as a local prototype. The first release focused on fact checks.\n"
        "== Features ==\nThe tool summarizes long pages. It also scans suspicious links."
    )

    async def fake_fetch(url: str) -> str:
        assert url == wiki_url
        return article

    monkeypatch.setattr(summarizer, "fetch_wikipedia_text", fake_fetch)

    def fake_get_cached(_key: str) -> None:
        return None

    def fake_set_cached(_key: str, _value: object) -> None:
        return None

    monkeypatch.setattr(main.db, "get_cached", fake_get_cached)
    monkeypatch.setattr(main.db, "set_cached", fake_set_cached)

    response = client.post("/api/summarize", json={"text": wiki_url})

    assert response.status_code == 200
    data = response.json()
    assert data["url"] == wiki_url
    assert [section["title"] for section in data["section_summaries"]] == ["History", "Features"]
    assert all(section["key_points"] for section in data["section_summaries"])

def test_versioned_routes():
    # FR-P4: API versioning
    r1 = client.post("/api/v1/verify/claim", json={"text": "Vaccine safety study confirms results."})
    assert r1.status_code == 200
    assert "claims" in r1.json()

    r2 = client.post("/api/v1/scan/url", json={"url": "https://google.com"})
    assert r2.status_code == 200
    assert r2.json()["level"] in ("Safe", "Caution")

def test_anonymous_access_allowed():
    # Anonymous requests work without Authorization header
    resp = client.post("/api/verify", json={"text": "A standard anonymous verification request."})
    assert resp.status_code == 200

def test_invalid_token_rejected():
    # Item 7: Backend rejects an expired or tampered token with 401
    resp = client.post(
        "/api/verify",
        json={"text": "Verification with bad token"},
        headers={"Authorization": "Bearer this.is.an.invalid.token"}
    )
    assert resp.status_code == 401

def test_history_requires_auth_or_absent():
    resp = client.get("/api/history")
    assert resp.status_code == 404

def test_cors_rejects_unknown_origin():
    resp = client.post(
        "/api/verify",
        json={"text": "A statement to verify."},
        headers={"Origin": "https://evil.example"},
    )
    assert "access-control-allow-origin" not in {key.lower(): value for key, value in resp.headers.items()}

def test_oversize_text_rejected():
    resp = client.post("/api/verify", json={"text": "x" * 5001})
    assert resp.status_code == 422


def test_oversize_url_rejected():
    resp = client.post("/api/scan", json={"url": "https://example.com/" + ("x" * 2040)})
    assert resp.status_code == 422


def test_no_fact_check_key_reuse(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "fact-check-only-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert not main.os.getenv("GEMINI_API_KEY")


def test_forged_jwt_rejected_in_all_modes(monkeypatch: MonkeyPatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    resp = client.post(
        "/api/verify",
        json={"text": "A statement to verify."},
        headers={"Authorization": "Bearer eyJhbGciOiJub25lIn0.eyJzdWIiOiJ4In0.x"},
    )
    assert resp.status_code == 401

def test_phase2_seed_corpus_does_not_invert_verdict():
    resp = client.post("/api/verify", json={"text": "Drinking colloidal silver cures viral infections."})
    assert resp.status_code == 200
    claim = resp.json()["claims"][0]
    assert claim["verdict"] == "Unverified"
    assert claim["sources"] == []
    assert "trust_score" not in claim

def test_phase3_crypto_drainer_detection():
    # FR-U7: Crypto drainer pattern detection
    resp = client.post("/api/scan", json={"url": "https://uniswap-v4-claim.airdrop-eth.xyz/permit2"})
    assert resp.status_code == 200
    data = resp.json()
    assert any("Crypto-drainer" in f for f in data["flags"])
    assert data["level"] == "Dangerous"
    assert "should_block" in data
    assert "telemetry" in data

def test_phase3_interstitial_endpoint():
    # FR-U8: Interstitial security barrier
    resp = client.get("/api/interstitial?url=https://malicious-test.xyz")
    assert resp.status_code == 200
    data = resp.json()
    assert "CRITICAL RISK" in data["warning"]
    assert data["can_proceed"] is True

def test_extension_interstitial_page_is_served():
    resp = client.get("/extension/interstitial.html")
    assert resp.status_code == 200
    assert "Deceptive or Malicious Site Ahead" in resp.text

def test_scan_safebrowsing_phishing_testbed():
    # Detects Google Safe Browsing phishing testbed and triggers Dangerous block
    resp = client.post("/api/scan", json={"url": "https://testsafebrowsing.appspot.com/s/phishing.html"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["level"] == "Dangerous"
    assert data["should_block"] is True
    assert "SOCIAL_ENGINEERING" in data["threats"]
    assert any("Known malware/phishing test signature" in f for f in data["flags"])
    assert any("Phishing" in f for f in data["flags"])

def test_history_never_contains_input():
    import sqlite3
    import db
    db.delete_history_data()
    with sqlite3.connect(db.DB_PATH) as conn:
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "trustlens_history" not in tables
        assert "history" not in tables


def test_cache_values_exclude_claim_text(monkeypatch: MonkeyPatch):
    test_verification_cache_excludes_claim_text(monkeypatch)


def test_expired_jwt_rejected(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("SUPABASE_URL", "https://mock.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "mock-service-key")

    async def mock_expired(*args: Any, **kwargs: Any) -> None:
        raise main.HTTPException(status_code=401, detail="Token rejected by authentication service")

    monkeypatch.setattr(main.supabase_client, "verify_token", mock_expired)
    resp = client.post(
        "/api/verify",
        json={"text": "A statement to verify."},
        headers={"Authorization": "Bearer expired.jwt.token"},
    )
    assert resp.status_code == 401


def test_supabase_outage_returns_503_not_trust(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("SUPABASE_URL", "https://mock.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "mock-service-key")

    async def mock_outage(*args: Any, **kwargs: Any) -> None:
        raise main.HTTPException(status_code=503, detail="Authentication service unavailable")

    monkeypatch.setattr(main.supabase_client, "verify_token", mock_outage)
    resp = client.post(
        "/api/verify",
        json={"text": "A statement to verify."},
        headers={"Authorization": "Bearer some.jwt.token"},
    )
    assert resp.status_code == 503


def test_authenticated_users_are_rate_limited(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("SUPABASE_URL", "https://mock.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "mock-service-key")

    async def mock_user(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"id": "rate-limit-user-123", "email": "test@example.com", "plan": "free"}

    monkeypatch.setattr(main.supabase_client, "verify_token", mock_user)
    monkeypatch.setattr(main, "GOOGLE_FACTCHECK_KEY", "")

    main.RATE_LIMIT_BUCKET.clear()

    for _ in range(30):
        r = client.post(
            "/api/verify",
            json={"text": "A statement to verify."},
            headers={"Authorization": "Bearer valid.token"},
        )
        assert r.status_code == 200

    r_blocked = client.post(
        "/api/verify",
        json={"text": "A statement to verify."},
        headers={"Authorization": "Bearer valid.token"},
    )
    assert r_blocked.status_code == 429
    assert "Retry-After" in r_blocked.headers


def test_no_key_reuse(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "fact-check-only-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert not main.os.getenv("GEMINI_API_KEY")


def test_oversize_input_rejected():
    resp_text = client.post("/api/verify", json={"text": "x" * 5001})
    assert resp_text.status_code == 422
    resp_url = client.post("/api/scan", json={"url": "https://example.com/" + ("x" * 2040)})
    assert resp_url.status_code == 422


def test_logs_contain_no_user_content(caplog: pytest.LogCaptureFixture, monkeypatch: MonkeyPatch):
    import logging
    import os
    import db
    marker = "MARKER-SECRET-7f3a"
    monkeypatch.setattr(main, "GOOGLE_FACTCHECK_KEY", "")
    with caplog.at_level(logging.DEBUG, logger="trustlens"):
        resp = client.post("/api/verify", json={"text": marker})
        assert resp.status_code == 200
        assert marker not in caplog.text
        if os.path.exists(db.DB_PATH):
            with open(db.DB_PATH, "rb") as f:
                db_bytes = f.read()
                assert marker.encode("utf-8") not in db_bytes
