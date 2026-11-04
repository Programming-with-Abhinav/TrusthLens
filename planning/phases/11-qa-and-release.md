# Phase 11 — QA, Load Testing & Release

**Goal:** prove it works, prove it fails safely, and ship with a rollback.
**Covers:** TL-060–062, 070 · QA-01–07 · all open requirements.
**Depends on:** Phases 5–10.

## Tasks
| ID | Task | Detail |
|---|---|---|
| 11.1 | Hermetic suite | All unit/integration tests run offline with mocks; isolated temp state; `pytest -m "not live"` is the default |
| 11.2 | Coverage | Backend ≥ 85% lines; ≥ 95% on auth, verdict mapping, rating table, privacy guards, SSRF guard, rate limiter; frontend ≥ 70% on logic components |
| 11.3 | CI pipeline | Required checks: ruff, mypy, pytest (+coverage), `pip-audit`, gitleaks, `npm ci && lint && typecheck && test && build`, `npm audit --omit=dev`, Playwright E2E, Lighthouse CI, Docker build + Trivy scan, extension build + manifest snapshot, docs check |
| 11.4 | Live smoke suite | Small `-m live` suite against staging with real keys: one claim, one URL, one summary, auth round trip; run before each release |
| 11.5 | Load test | k6: ramp to the agreed RPS (set from D7 caps × expected users; start with 20 RPS) for 15 min; assert p95 latencies and error rate < 1% |
| 11.6 | Chaos drills | Redis down, Supabase slow/down, Google API 5xx/timeouts, Gemini failure: confirm degraded modes are clear to users and safe |
| 11.7 | Security test | Run `SECURITY-CHECKLIST.md`; OWASP ZAP baseline scan on staging; manual test of auth bypass, IDOR on tokens/usage, open redirect, XSS in rendered results, SSRF |
| 11.8 | Docs truthfulness | Script or review comparing docs claims to code (feature list, versions, ports, env vars); update README, privacy policy, `STATE.md` |
| 11.9 | Release candidate | Tag `v1.1.0-rc1`; deploy to staging; run `RELEASE-CHECKLIST.md` end to end with a second person |
| 11.10 | Launch | Deploy to production per runbook; canary then full; monitor 60 min; announce only after green |
| 11.11 | Post-launch | 7-day watch: error budget, cost, support inbox; write retro; schedule v1.2 (billing, semantic retrieval) |

## Exit gate
`RELEASE-CHECKLIST.md` 100% ticked with evidence · rollback rehearsed · on-call named for first 7 days.
