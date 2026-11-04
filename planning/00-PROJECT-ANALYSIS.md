# 00 — Project Analysis (as of 2026-10-24)

## 1. What TrustLens is

A browser-first protection tool with two jobs: (a) check factual claims, (b) assess URL safety, plus a user-triggered page summarizer. Surfaces: Chrome MV3 extension, FastAPI backend, Next.js 16 website/dashboard with Supabase auth, and a static demo UI served by the API.

## 2. Architecture as built

| Component | Technology | Evidence level | State |
|---|---|---|---|
| API gateway | FastAPI, `main.py` (496 lines) | **Read** | Works as a demo; auth, privacy and rate limiting are unsafe for public use |
| Claim engine | `claims_engine.py` | **Read** | Keyword/regex logic presented as NLI + embeddings; 7 seeded records |
| URL engine | `url_scanner.py` + heuristics in `main.py` | **Read** | Functional; false-positive and blocking-I/O problems |
| Summarizer | `summarizer.py` | **Read** | Best-built module; keep |
| Persistence | `db.py`, SQLite `trustlens.db` | **Read** + DB inspected | Stores raw claims/URLs; no TTL; no volume |
| Auth/usage | `supabase_client.py` | **Read** | Fails open; racy counters |
| Tests | `test_main.py` (24 tests) | **Read** | Live-network dependent; important gaps |
| Container | `Dockerfile`, `docker-compose.yml` | **Read** | Dev-grade |
| Chrome extension | `extension/` | **Not seen** | Unknown; docs describe it |
| Static demo UI | `static/` | **Not seen** | Unknown |
| Next.js app | `my-vibe-app/` | **Not seen** | Unknown; `middleware.ts` is deprecated in Next 16 |
| SQL migrations / schema | `migrations/`, `supabase/schema.sql` | **Not seen** | Unknown; RLS unverified |
| CI | `.github/workflows/ci.yml` | **Not seen** | Unknown |

## 3. Demo → production gap

| Dimension | Demo today | Production target |
|---|---|---|
| Privacy | Raw claims/URLs in SQLite, readable via public `/api/history` | Zero raw user content stored or logged; hashed cache keys only |
| Auth | Unsigned JWTs accepted when Supabase is off/unreachable/errors | Fail closed; signature verified; per-user limits |
| Truth results | Top-1 weak match accepted; verdict mapping can invert; fake confidence | Only evidence-backed verdicts; explicit "Unverified"; calibrated labels |
| Honesty of claims | Docs say NLI cross-encoder, dense embeddings | Features named for what they do, or really built |
| URL scanning | Substring brand/TLD rules flag trusted sites | Allowlist-tested, scored, explained, near-zero FP on top domains |
| Performance | Sequential claims, blocking socket/SQLite in async routes | Parallel, async, p95 within target with measured proof |
| Rate limiting | In-memory, per-process, proxy-blind | Redis sliding window per user/IP, trusted-proxy aware |
| Storage | SQLite on container disk | Redis cache with TTL; Postgres for accounts/usage |
| Deploy | `COPY . .` as root, unpinned deps, no health split | Pinned, non-root, secrets injected, readiness/liveness, rollback |
| UI | Static demo page + dashboard of unknown quality | Designed system, all states, WCAG 2.1 AA, responsive |
| Extension | Manual token paste, permissions unverified | Safe auth link, least-privilege manifest, Store-ready |
| Process | "Verified 100%" with no evidence | Evidence-gated completion, CI, release checklist |

## 4. Defect register

Severity: **Crit** = leaks data / wrong answers presented as fact / auth bypass. **High** = breaks a stated requirement or will fail in production. **Med** = quality/ops. **Low** = polish.
"Proof" = the test that must exist and pass to close the item.

### 4.1 Security & privacy
| ID | Sev | Where | Problem | Fix | Proof | Phase |
|---|---|---|---|---|---|---|
| TL-001 | Crit | `main.py` → `db.add_history_entry` | Stores first 80 chars of raw claim text and URL. Verified in `trustlens.db` (e.g. a COVID claim, a localhost URL). Violates PROJECT.md privacy rule | Delete history feature or store only `{type, verdict, timestamp}`; purge existing DB | `test_history_never_contains_input` | 5 |
| TL-002 | Crit | `GET /api/history` | Unauthenticated; returns everyone's entries | Remove endpoint (or auth + per-user + no content) | `test_history_requires_auth_or_absent` | 5 |
| TL-003 | Crit | `verify_single_claim` cache | Cached JSON includes full `claim` text | Cache only `{verdict, sources, …}` keyed by SHA-256 of normalized claim; re-attach claim from request | `test_cache_values_exclude_claim_text` | 5/8 |
| TL-004 | Crit | `supabase_client.verify_token` | If Supabase unconfigured, unreachable, or returns non-200/401, unsigned token payload is trusted. Any `a.b.c` with a `sub` passes | Fail closed. Verify signature via JWKS or Supabase `/auth/v1/user`; any error → 401/503 | `test_forged_jwt_rejected_in_all_modes` | 5 |
| TL-005 | High | verify/scan/summarize routes | Any authenticated caller skips rate limiting entirely | Rate-limit every caller; per-user + per-IP | `test_authenticated_users_are_rate_limited` | 5/8 |
| TL-006 | High | CORS in `main.py` | `allow_origins=["*"]` with `allow_credentials=True` | Allowlist website origin + `chrome-extension://<id>`; no credentials needed for Bearer | `test_cors_rejects_unknown_origin` | 5 |
| TL-007 | High | `Dockerfile` | `COPY . .` with no `.dockerignore` can bake `.env`, `.venv`, DB into image; root user | `.dockerignore`, multi-stage, non-root, read-only FS | CI image scan + `test_image_has_no_env_file` | 5/8 |
| TL-008 | Med | `_env.example`, `.gitignore` | Example contains a real Supabase project URL; ignore list covers only `.env` | Placeholder values; ignore `.env*` except example; rotate any exposed keys | gitleaks in CI | 5 |
| TL-009 | High | `claims_engine.synthesize_grounded_explanation` | Falls back to the Fact Check key as the Gemini key | Separate `GEMINI_API_KEY` only | `test_no_key_reuse` | 5 |
| TL-010 | Med | `url_scanner.check_ssl_certificate`, RDAP | Server connects to any user-supplied host (SSRF-style probing) | Resolve DNS, block private/loopback/link-local/metadata ranges, fixed port 443, strict timeouts | `test_ssrf_targets_blocked` | 7 |
| TL-011 | Med | logging in `main.py` | Exception strings can contain URLs/keys; JSON format string breaks on quotes | `structlog`/JSON formatter, redaction filter, never log request bodies | `test_logs_contain_no_user_content` | 5/8 |
| TL-012 | High | extension auth (docs) | User pastes a Supabase access token that expires (~1h) | Revocable extension tokens or secure link flow (see DECISIONS D6) | e2e: token revoke works | 10 |

### 4.2 Truth engine
| ID | Sev | Where | Problem | Fix | Proof | Phase |
|---|---|---|---|---|---|---|
| TL-020 | Crit | `hybrid_search` + `verify_single_claim` | Weak lexical overlap (cosine>0.08 or BM25>0.1) over 7 records; top hit accepted with hardcoded 0.92 confidence. "Water boils at 100°C" can inherit the colloidal-silver "False" verdict | Raise thresholds, require claim↔record entailment/similarity above calibrated cutoff, else "Unverified". Label seed data "demo" only | golden-set test of 50 unrelated claims → all Unverified | 6 |
| TL-021 | Crit | `map_verdict` | "false" words checked first, then "true"/"accurate" → "Not true", "Inaccurate", "Half true", "Partly true" become **Verified**; unknown ratings default to "Mixed" | Explicit rating table + ordered negation-aware rules; unknown → "Unrated" | table-driven test of ≥60 real rating strings | 6 |
| TL-022 | High | `classify_nli_stance` | Regex on the rating text; stance just restates verdict. Docs claim cross-encoder NLI | Either implement real NLI (claim vs evidence snippet) or remove "NLI" naming and stance field | `test_stance_not_derived_from_rating_alone` or docs diff | 6 |
| TL-023 | High | `build_vector_representation` | Word-count cosine, not embeddings; corpus is 7 hardcoded records; no ingestion | Primary source = Google Fact Check API; semantic layer deferred to v1.2 with a real corpus | docs/requirements updated | 6 |
| TL-024 | High | `confidence`, `trust_score` | Confidence is vote share or constant; score implies precision that does not exist | Replace with labelled bands + evidence count; remove numeric "truth score" from UI | UI snapshot + API contract test | 6/9 |
| TL-025 | High | `db` cache | No TTL; caches "No evidence found" and demo results forever; key ignores mode, case, whitespace | Normalize before hashing; TTL (e.g. 24h found / 1h not found); include source mode in key | `test_cache_ttl_and_mode_isolation` | 6/8 |
| TL-026 | Med | `split_claims` | Drops claims with <4 words when any longer sentence exists; naive split on abbreviations | Keep ≥3-word claims; better sentence splitter; cap total chars | claims unit tests | 6 |
| TL-027 | Med | `verify_claims` | Claims verified sequentially; worst case ≈ 5×(8s+6s); synthesis capped at 100 tokens (truncates) | `asyncio.gather` with per-call budget; overall deadline; sane token limit | latency test with mocked slow upstreams | 6/8 |
| TL-028 | Med | synthesis prompt | Only quotes/newlines stripped; evidence text unsanitized; output unchecked | Delimit untrusted text, strip control chars, validate output length/format, never follow instructions in sources | injection test set | 6 |
| TL-029 | Low | `compute_temporal_decay` | Comment says half-life 4 years; formula gives ≈7.6 years; naive `datetime.now()` | Correct doc or constant; use UTC | unit test | 6 |
| TL-030 | Med | `DEMO_DATABASE` | Any claim containing "vaccine" returns "Misleading" in demo mode, including true statements | Remove from production path; demo mode must be explicit and badged | `test_demo_mode_never_default_in_prod` | 6 |

### 4.3 URL scanner
| ID | Sev | Where | Problem | Fix | Proof | Phase |
|---|---|---|---|---|---|---|
| TL-040 | High | `analyze_url_heuristics` | Substring brand match flags `google.co.in`, `amazon.in`, `paypal.me`; "login"/"secure" in host and `.ru` are flagged; "sbi" matches unrelated hosts | Use registrable-domain (Public Suffix List) + official-domain map per brand; score signals, don't block on one | top-1000 domain test: 0 Dangerous, ≤1% flagged | 7 |
| TL-041 | High | `lookup_domain_age` | RDAP asked for full hostname (subdomains fail); unbounded in-memory cache | Query registrable domain; TTL cache (Redis); record "unknown" explicitly | mocked RDAP tests incl. subdomains | 7 |
| TL-042 | High | `check_ssl_certificate`, `db` calls | Blocking socket (3 s) and sync SQLite inside async routes stall the event loop | `asyncio.open_connection`/thread pool; async or threadpool DB | concurrency test: 50 parallel scans, p95 target | 7/8 |
| TL-043 | Med | `validate_and_normalize_url` | `ftp://` etc. accepted; no userinfo (`user@host`) flag, no shortener/redirect handling; response echoes raw input | Allow only http/https; add flags; normalize/IDNA | validation tests | 7 |
| TL-044 | Med | `scan_url` level logic | One signal (e.g. "phish" in path) → "Dangerous"/block; thresholds arbitrary | Weighted score → Safe/Caution/Suspicious/Dangerous with documented weights; block only on corroborated or Web Risk hit | scoring table tests | 7 |
| TL-045 | Med | `/api/interstitial` | Returns same static "CRITICAL RISK" JSON for any URL; `can_proceed` always true | Remove or make it evaluate the URL; the real interstitial belongs to the extension | endpoint test | 7/10 |
| TL-046 | Med | Web Risk call | Failures silent; response doesn't say the live check was skipped | Return `checks: {web_risk: ok|skipped|failed}` | contract test | 7 |

### 4.4 API & infrastructure
| ID | Sev | Where | Problem | Fix | Proof | Phase |
|---|---|---|---|---|---|---|
| TL-050 | High | `check_ip_rate_limit` | In-memory dict, never evicted, per-process, sees proxy IP only, counts rejected hits | Redis sliding window; trusted-proxy aware client IP | multi-worker test | 8 |
| TL-051 | High | `db.py` | SQLite on container disk (lost on redeploy); `init_db()` at import can crash startup | Redis (cache) + Postgres (accounts/usage); explicit startup/migration step | restart-persistence test | 8 |
| TL-052 | High | `supabase_client.record_*` | Read-modify-write loses concurrent increments; summaries uncounted | Atomic SQL RPC `increment_usage`; count all three feature types | concurrency test | 8 |
| TL-053 | Med | routing | `/api/summarize`, `/api/history`, `/api/interstitial` lack `/api/v1` aliases | One router mounted at both prefixes | route-parity test | 8 |
| TL-054 | Med | `main.py` mounts | API serves `static/` and `extension/` with relative paths | API-only in prod; website is Next.js; extension ships via Store | prod image has no static dirs | 8 |
| TL-055 | Med | `requirements.txt` etc. | Unpinned, pytest in prod deps; Python 3.11 (Docker) vs 3.12+ (docs) vs 3.14 (`_clinerules`) | Lockfile, `requirements-dev.txt`, one Python version everywhere | CI matrix | 8 |
| TL-056 | Med | `/api/health` | Pings Supabase on every call; no liveness/readiness split | `/healthz` (cheap) and `/readyz` (deps, cached) | endpoint tests | 8 |
| TL-057 | Med | `TextRequest`, `UrlRequest` | No `max_length` (only summarizer has one) | Limits: text ≤ 5,000, URL ≤ 2,048; body-size cap at proxy | oversize tests → 413/422 | 5/8 |
| TL-058 | Med | startup | No config validation; silent demo-mode fallback | Typed settings (pydantic-settings); production refuses to start if required secrets missing | startup test | 8 |
| TL-059 | Low | cache key | MD5 | SHA-256 | unit test | 8 |

### 4.5 Tests, docs, web, extension
| ID | Sev | Where | Problem | Fix | Phase |
|---|---|---|---|---|---|
| TL-060 | High | `test_main.py` | Several tests call live RDAP/SSL; `test_phase2` depends on env keys and a persisted cache | Mock all network; isolated temp DB; fixtures reset state | 11 |
| TL-061 | High | `test_main.py` | No tests for: 429 limit, valid-token path, usage increment, `claims_engine` units, DB migrations, Gemini path, `supabase_client` | Add per TEST-PLAN.md | 11 |
| TL-062 | Med | CI | Workflow not seen; claims "operational" | Audit and rebuild per TEST-PLAN.md §CI | 11 |
| TL-070 | Med | planning docs | Contradictions listed in the first review; "Verified 100%"; test counts 11/15/24 | Replace with this folder | 5 |
| TL-071 | Med | code comments | Three phase-numbering schemes (PRD, `.planning`, `state.json`); PRD files referenced but not provided | One scheme (this roadmap); add PRD or remove references | 5 |
| TL-072 | Med | requirements | Summarizer (FR-S1–S9) and "workbench" have no requirement entries here | Added as REQ-SUM-* | 5 |
| TL-080 | Med | `my-vibe-app/middleware.ts` | Deprecated in Next.js 16; renamed `proxy.ts` (Node runtime) | Run `npx @next/codemod@canary middleware-to-proxy .`; re-test route gating | 9 |
| TL-081 | Low | PROJECT.md | "Node.js 18+" but Next 16 needs Node 20.9+ | Update; pin in `.nvmrc`/`engines` | 9 |
| TL-082 | High | extension manifest | FR-E5 says only `activeTab`+`storage`, but interception/background features normally need more. **VERIFY** | Audit manifest; justify each permission or remove feature | 10 |
| TL-083 | Med | dashboard | Quota bar shown although plans are "unlimited". **VERIFY** | Remove or reflect real limits | 9 |
| TL-084 | Med | `static/` | Demo UI served at `/` | Retire; workbench lives in Next.js | 9 |

## 5. Documentation vs reality (remove or rewrite)

| Claim | Reality | Action |
|---|---|---|
| Cross-encoder NLI stance | Regex on rating text | Rename ("rating-derived stance") or build NLI |
| Dense vector embeddings | Word-count cosine | Rename or build |
| "Ingest ClaimReview datasets" | 7 hardcoded records | Remove claim |
| "Sanitized history", "no claim text stored" | Raw text stored | Fix code (TL-001) then restate |
| "Complete & Verified, 15/15 tests" | 24 tests, none against live keys or extension | Replace with evidence-based STATE.md |
| "Half-life ≈ 4 years" | ≈ 7.6 years | Fix |
| "Free tier + future Pro" vs "100% free, unlimited" | Code has no quotas | DECISIONS D7 |

## 6. Strengths worth keeping
Dual route aliases; Web Risk only called when keyed (tested); summarizer design (Wikipedia host allowlist, no redirects, hash-only cache, extractive fallback); closed Shadow DOM and no-`innerHTML` rules (stated, **VERIFY** in code); CodeRabbit path rules; privacy-by-design intent.

## 7. Not audited (Phase 5, task 5.0)
`extension/*`, `static/*`, `my-vibe-app/*`, `supabase/schema.sql`, `migrations/*.sql`, `.github/workflows/*`, real `.env`, any `.dockerignore`. Each gets a written audit note before Phase 9/10 starts.
