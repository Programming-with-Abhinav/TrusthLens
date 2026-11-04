# Project: TrustLens AI — v1.1 Production Readiness

## What it is
TrustLens helps people judge online claims and links without leaving the page. It checks claims against published fact-checks, scans URLs for phishing/scam signals, and (on request) summarizes a page. It ships as a Chrome extension, a website with accounts, and an API.

## What it is not
- Not an arbiter of truth. It reports what fact-checkers have published and says "Unverified" otherwise.
- Not a guarantee of URL safety. It reports risk signals with reasons.
- Not a browsing-history product. It does not keep what users check.

## Core value
Fast, honest, privacy-preserving answers inside the browser: *what do fact-checkers say, and is this link risky — and why.*

## Users
Everyday users, students, researchers, and people exposed to crypto and payment scams.

## Production success criteria (measurable)
| Metric | Target | Measured by |
|---|---|---|
| Claim verify latency (single claim, warm) | p95 ≤ 2.0 s; cache hit p95 ≤ 300 ms | k6 load test (Phase 11) |
| URL scan latency | p95 ≤ 1.5 s | k6 |
| False "Dangerous" on top-1000 domains | 0 | Allowlist test (Phase 7) |
| Wrong-verdict rate on golden set | 0 verdict inversions; ≥ 95% agreement with source rating | Golden set (Phase 6) |
| Raw user content stored/logged | 0 bytes | Privacy tests + log audit |
| Availability | ≥ 99.5% monthly | Uptime monitor |
| Accessibility | WCAG 2.1 AA, 0 critical axe findings | axe + manual (Phase 9) |
| Web vitals (site) | LCP ≤ 2.5 s, CLS ≤ 0.1, INP ≤ 200 ms | Lighthouse CI |

## Privacy rules (non-negotiable)
1. Raw claims, page text and visited URLs are never written to disk, database or logs.
2. Only aggregate per-user daily counts are stored (claim checks, URL scans, summaries).
3. Third-party calls are disclosed in the privacy policy: Google Fact Check Tools (claim text), Google Web Risk (URL), RDAP (domain), Gemini (text sent for summary/explanation, only when the user triggers it).
4. Users can delete their account and all associated data in-app.

## Constraints
Chrome MV3 · Python 3.12 (single version everywhere) · Node 20.9+ (Next.js 16) · No `innerHTML` in extension/static code · Closed Shadow DOM for overlays · Least-privilege extension permissions.

## Out of scope for v1.1
Stripe billing, Pro/Team plans, Firefox/Safari builds, semantic retrieval over a private corpus, Kubernetes, mobile apps.

## Key decisions
See `DECISIONS.md`. The API is the single gateway; the Next.js app owns the website, accounts and dashboard; Supabase owns auth/usage; Redis owns cache and rate limits.
