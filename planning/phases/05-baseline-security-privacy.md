# Phase 5 — Baseline, Security & Privacy (P0) [COMPLETED]

**Goal:** stop data exposure and auth bypass, freeze a trustworthy baseline, and replace misleading docs.
**Covers:** TL-001, 002, 003, 004, 005, 006, 007, 008, 009, 011, 057, 070, 071, 072 · SEC-01–05 · PRIV-01–04.
**Status:** Completed. All proof tests green. Unseen code audited in `audits/PHASE-5-CODE-AUDIT.md`.
**Rule:** nothing from Phases 6–10 merges before this phase's exit gate.

## Tasks
| ID | Task | Detail | Status |
|---|---|---|---|
| 5.0 | **Audit unseen code** | Read `extension/`, `static/`, `my-vibe-app/`, `supabase/schema.sql`, `migrations/`, `.github/workflows/`, `.dockerignore`. Recorded in `audits/PHASE-5-CODE-AUDIT.md` | Completed |
| 5.1 | Branch + tag | Tag `demo-final`. Create `release/v1.1` | Completed |
| 5.2 | Purge stored content | Delete `trustlens.db` from repo/history/images. Check git history (`git log --all -- trustlens.db`); ignored via `.gitignore` and `.dockerignore` | Completed |
| 5.3 | Remove history storage | Delete `add_history_entry` calls in `main.py` and the `trustlens_history` table usage. Remove `GET /api/history`. Proof test verified | Completed |
| 5.4 | Cache without content | Store `{verdict, sources, synthesis, checked_at}` only; key = SHA-256 of normalized claim. Re-attach `claim` from the request when responding | Completed |
| 5.5 | Fail-closed auth | Rewrite `verify_token`: (a) verify signature + `exp` + `aud` via Supabase JWKS (cached) or `/auth/v1/user`; (b) no `_decode_jwt_unverified` for authorization; (c) Supabase unreachable → 503 for token requests; (d) unconfigured Supabase in production → refuse boot, in dev → reject tokens. | Completed |
| 5.6 | Rate-limit everyone | Per-user and per-IP buckets for `verify`, `scan`, `summarize`; return `429` + `Retry-After`. Clean stale entries automatically | Completed |
| 5.7 | CORS allowlist | Settings-driven origins (site + `chrome-extension://<id>`); `allow_credentials=False` (Bearer header needs none) | Completed |
| 5.8 | Secrets hygiene | `.env.example` with placeholders only; `.gitignore` covers `.env*` except example; `.dockerignore` hardened | Completed |
| 5.9 | Separate LLM key | Remove fallback from `GOOGLE_FACTCHECK_API_KEY`/`GOOGLE_API_KEY` to Gemini in `claims_engine.py`; only `GEMINI_API_KEY` | Completed |
| 5.10 | Input limits | `max_length` on `TextRequest`/`UrlRequest`; reject oversize with 422; document limits | Completed |
| 5.11 | Log hygiene | Replace string-formatted JSON logger; filter drops request bodies; never log raw keys or user inputs | Completed |
| 5.12 | Replace planning docs | Adopt production planning docs; rename references; fix versions | Completed |
| 5.13 | Baseline tests | Proof tests added; 46 backend tests pass cleanly | Completed |

## Proof tests (must exist and pass)
`test_history_never_contains_input` · `test_history_requires_auth_or_absent` · `test_cache_values_exclude_claim_text` · `test_forged_jwt_rejected_in_all_modes` · `test_expired_jwt_rejected` · `test_supabase_outage_returns_503_not_trust` · `test_authenticated_users_are_rate_limited` · `test_cors_rejects_unknown_origin` · `test_no_key_reuse` · `test_oversize_input_rejected` · `test_logs_contain_no_user_content` (captures logs during a request containing a unique marker string and asserts the marker never appears in logs, DB file bytes, or cache values).

## Verification (by a second person)
1. Run the marker test manually: submit `MARKER-7f3a` as claim and URL; `grep -a MARKER` the DB files, logs, and Redis/SQLite dumps → zero hits.
2. Send `Authorization: Bearer eyJhbGciOiJub25lIn0.eyJzdWIiOiJ4In0.x` in demo, configured and Supabase-down modes → never 200.
3. `curl -H "Origin: https://evil.example"` → no `Access-Control-Allow-Origin` echo.
4. `docker build` then `docker run --rm image ls -a /app` → no `.env`, no `*.db`.
5. gitleaks over full history → clean (or exposed keys rotated and noted).

## Exit gate
All proof tests green in CI · manual verification signed · `STATE.md` updated with evidence · critical TL items closed.
