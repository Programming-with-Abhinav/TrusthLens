# Phase 8 — API Production Hardening

**Goal:** make the gateway stateless, observable, safe to scale, and deployable.
**Covers:** TL-005, 007, 050–059 · API-01–10 · SEC-02, 07, 08 · TRUTH-06 (storage) · PRIV-04.
**Depends on:** Phases 5, 6, 7 · DECISIONS D1, D3, D7.

## Tasks
| ID | Task | Detail |
|---|---|---|
| 8.1 | Typed settings | `pydantic-settings` class; `ENV=production` requires: Supabase URL/keys, Redis URL, allowed origins, Fact Check key. Boot fails with a clear message otherwise. No silent demo fallback in production |
| 8.2 | Redis | Add Redis client (async). Use for: cache (TTL), rate limits (sliding window via Lua or `INCR`+`EXPIRE`), RDAP cache. Remove SQLite and `db.py` import-time migrations |
| 8.3 | Rate limiting | Key by user id when authenticated, else client IP. Client IP only from trusted proxy headers (`--proxy-headers`, `--forwarded-allow-ips` set to the platform's proxy) — never trust arbitrary `X-Forwarded-For`. Separate limits per route; 429 with `Retry-After`; per-user daily caps from D7 |
| 8.4 | Usage counting | Postgres RPC `increment_usage(user_id, day, kind)` using `INSERT … ON CONFLICT DO UPDATE SET n = n + 1`; call after a successful response; include summaries. Backend uses service-role key server-side only. Verify RLS still blocks cross-user reads |
| 8.5 | Route versioning | One `APIRouter` mounted at `/api/v1` and legacy `/api` (legacy responses add `Deprecation: true`). Include summarize and health. Remove history |
| 8.6 | API-only app | Remove `StaticFiles` mounts and favicon route; gate `/docs` and `/openapi.json` behind a flag (off in production) |
| 8.7 | Health | `/healthz` returns 200 immediately; `/readyz` checks Redis and (cached 30 s) Supabase; neither pings third-party APIs on each call |
| 8.8 | Error contract | Global exception handlers → `{code, message, request_id}`; no tracebacks; map upstream failures to 502/503 with safe messages |
| 8.9 | Observability | Request-ID middleware; JSON logs; Sentry (or equivalent) with `before_send` scrubbing; basic metrics (request count, latency histogram, upstream error rate) |
| 8.10 | Security headers | `Strict-Transport-Security`, `X-Content-Type-Options`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` on authenticated responses |
| 8.11 | Container | Multi-stage build, `python:3.12-slim` pinned by digest, non-root user, `HEALTHCHECK`, no dev deps, `--workers` set from CPU, graceful shutdown |
| 8.12 | Dependencies | `requirements.in` → locked `requirements.txt` (pip-tools/uv) + `requirements-dev.txt`; `pip-audit` in CI; Dependabot/Renovate |
| 8.13 | Lint/type | `ruff`, `mypy` (or pyright) in CI; fix findings |
| 8.14 | Staging | Provision staging with real keys on separate Supabase project and Redis; deploy per `DEPLOYMENT-RUNBOOK.md` |
| 8.15 | Budget guard | Cost alarms on Google/Gemini usage; hard per-day request ceilings |

## Proof tests
`test_prod_refuses_to_boot_without_config` · `test_rate_limit_shared_across_workers` (two app instances, one Redis) · `test_usage_increment_is_atomic` (100 concurrent requests → count 100) · `test_summaries_are_counted` · `test_legacy_and_v1_route_parity` · `test_no_static_mounts_in_prod` · `test_readyz_degrades_when_redis_down` · `test_error_contract_has_request_id` · `test_security_headers_present` · image checks: runs as non-root, `HEALTHCHECK` passes.

## Verification
Deploy to staging; run the Phase 5 manual checks again; kill Redis and confirm clean 503s and recovery; roll a new image and confirm no data loss other than cache.

## Exit gate
Staging healthy for 48 h under synthetic traffic · alerts fire in a drill · rollback rehearsed once.
