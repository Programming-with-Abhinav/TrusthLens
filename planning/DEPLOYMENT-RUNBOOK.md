# Deployment Runbook

Adjust names to the hosting chosen in DECISIONS D1. Defaults below assume: Next.js on Vercel (or similar), API container on a managed platform, Supabase (Auth + Postgres), managed Redis.

## 1. Environments
| Env | Purpose | Data | Keys |
|---|---|---|---|
| local | development | fakes/mocks, optional real keys | personal |
| staging | release candidate, parity with prod | separate Supabase project and Redis | separate, low quotas |
| production | users | production Supabase/Redis | production only |
Never share keys, projects or databases between staging and production.

## 2. Configuration (API)
| Variable | Required in prod | Notes |
|---|---|---|
| `ENV` | yes | `production` enables strict boot checks |
| `GOOGLE_FACTCHECK_API_KEY` | yes | restrict by API (Fact Check Tools) in Google Cloud |
| `GOOGLE_WEB_RISK_API_KEY` | recommended | separate key; billing alert (free tier then billable) |
| `GEMINI_API_KEY` | if D8=a | separate key; budget alert |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | yes | service key server-side only |
| `SUPABASE_JWT_AUDIENCE`/JWKS URL | yes | for local JWT verification |
| `REDIS_URL` | yes | TLS URL |
| `ALLOWED_ORIGINS` | yes | site origin + `chrome-extension://<id>` |
| `TRUSTED_PROXY_IPS` | yes | for correct client IP |
| `SENTRY_DSN` | recommended | scrubbing enabled |
| `LOG_LEVEL` | no | default INFO |
Web app: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (public), `NEXT_PUBLIC_API_BASE_URL`; server-only: `SUPABASE_SERVICE_ROLE_KEY`. Confirm the exact variable names against the code at Phase 5.

## 3. One-time setup
1. Register domain; DNS for `site` and `api` subdomains; TLS via platform.
2. Create Supabase prod project; apply schema/migrations; enable email confirmation; configure Google OAuth redirect URLs for prod domain only; verify RLS policies with the SECURITY-CHECKLIST tests.
3. Provision Redis (TLS, password, maxmemory policy `allkeys-lru` for cache).
4. Google Cloud: restrict each API key by API and (where possible) by IP/referrer; set quotas and billing alerts.
5. Sentry project, uptime monitor on `/healthz` (API) and `/` (site), alert routing to a named on-call.
6. Store secrets in the platform secret manager; no secrets in repo or CI logs.

## 4. Release procedure
1. Merge to `release/v1.1`; CI green; tag `vX.Y.Z-rcN`.
2. Build image; scan; push with immutable tag.
3. Deploy to staging; run migrations (explicit step, not at app import); run live smoke + `RELEASE-CHECKLIST.md`.
4. Promote the same image digest to production: canary 10% for 15 min → 100%.
5. Watch dashboards 60 min: error rate, p95 latency, 429 rate, upstream failures, cost.
6. Tag final, update changelog, notify.

## 5. Rollback triggers (decide now, not during an incident)
5xx > 2% for 5 min · p95 verify > 4 s for 10 min · auth failures spike > 3× baseline · any confirmed data exposure · wrong-verdict report verified by a human.
**Rollback:** redeploy previous image digest (keep last 3); database migrations must be backward compatible for one release (expand → migrate → contract). Cache can be flushed safely.

## 6. Incident basics
Severity: S1 data exposure or auth bypass (page immediately, disable affected endpoint, rotate keys, notify per legal advice) · S2 wrong verdicts or major outage · S3 degraded. Keep a timeline; write a blameless postmortem within 5 days.

## 7. Operations
Daily: error and cost dashboards. Weekly: dependency PRs, quota review. Monthly: key rotation review, restore test of Postgres backup, access review.
Extension: staged Store rollout; keep previous zip; version the backend API so older extension versions keep working for ≥ 2 releases.
