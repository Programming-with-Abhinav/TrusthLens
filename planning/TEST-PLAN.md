# Test Plan

## 1. Principles
Hermetic by default · test behaviours that can hurt users (wrong verdicts, leaks, false alarms) first · every closed defect gets a regression test · tests are deterministic (no live network, fixed clocks, isolated state).

## 2. Pyramid and tooling
| Layer | Tooling | Scope |
|---|---|---|
| Unit | pytest, respx/monkeypatch, freezegun | verdict table, claim splitting, scoring, SSRF guard, rate limiter, cache keys, redaction |
| Integration | FastAPI TestClient, fakeredis, test Postgres (or mocked Supabase) | routes, auth modes, usage atomicity, error contract |
| Contract | OpenAPI schema tests / schemathesis | response shapes, versions parity |
| Frontend unit | Vitest + Testing Library | components, states |
| E2E | Playwright (web + persistent context for extension) | user journeys |
| Accessibility | axe-core in Playwright, manual NVDA/VoiceOver | all routes |
| Performance | Lighthouse CI, k6 | budgets, latency, load |
| Security | gitleaks, pip-audit, npm audit, Trivy, ZAP | see SECURITY-CHECKLIST |
| Live smoke | pytest `-m live` | real keys on staging, on demand |

## 3. Datasets (create in Phase 6/7; store under `tests/data/`)
- **Rating strings** (≥ 60): real `textualRating` values with expected verdict.
- **Claims golden set** (50): 25 with known fact-checks (expected verdict) and 25 unrelated/true statements (expected Unverified).
- **Injection set** (≥ 20): attempts inside claims and evidence.
- **Trusted domains** (top 1,000 snapshot) + extra: Indian banks (e.g. sbi.co.in, hdfcbank.com), government (`.gov.in`), universities, e-commerce, CDNs.
- **Known-bad samples:** Google Safe Browsing test pages and synthetic look-alikes only.
- **SSRF targets:** loopback, RFC1918, link-local, metadata IP, IPv6 forms, decimal/hex IPs, DNS names resolving to private IPs (mocked resolver).

## 4. Required test cases (beyond Phase files)
**Auth:** valid token → user counted · expired · wrong audience · bad signature · `alg:none` · Supabase 5xx · concurrent first-login.
**Rate limit:** boundary (limit, limit+1) · window rollover · per-user vs per-IP · proxy header spoof ignored.
**Verify:** 1/5/6 claims · empty/whitespace · unicode/RTL/emoji · 5,001 chars · partial timeout · cache hit/miss/TTL expiry · Google 429/500 · malformed upstream JSON.
**Scan:** IDN homographs · punycode · userinfo trick (`https://google.com@evil.xyz`) · IPv6 literal · very long URL · shorteners (flag, don't resolve) · redirects not followed server-side.
**Summarize:** 50k boundary · injection text · Wikipedia host allowlist bypass attempts (`wikipedia.org.evil.com`, `@`, ports) · Gemini invalid JSON → extractive fallback.
**Privacy:** marker string across DB, Redis dump, logs, error tracker payload mock.
**Frontend:** each state per component · form validation · `next` redirect safety · SSR gating without session · client bundle contains no service-role key.
**Extension:** pill lifecycle · Esc/keyboard · no pre-click network · interstitial gating and escape · token revoke · permission snapshot.

## 5. CI pipeline (all required for merge)
1. `ruff` + `mypy` · 2. `pytest -m "not live" --cov` (thresholds in QA-02) · 3. `pip-audit` · 4. `gitleaks` · 5. `npm ci` → `lint` → `typecheck` → `vitest` → `build` · 6. `npm audit --omit=dev` · 7. Playwright E2E (web, extension) · 8. Lighthouse CI · 9. Docker build + Trivy · 10. Manifest snapshot check · 11. Docs check.
Nightly: live smoke against staging, ZAP baseline, dependency update PRs.

## 6. Exit criteria
No open Critical/High defects · coverage thresholds met · all E2E green three runs in a row · load test meets targets · security checklist signed.

## 7. Defect handling
Report with ID, steps, expected/actual, evidence. Fix → add regression test → reviewer confirms → log in `STATE.md`.
