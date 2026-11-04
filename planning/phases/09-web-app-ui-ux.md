# Phase 9 — Web App UI/UX (Next.js 16 + Supabase)

**Goal:** a trustworthy, accessible, fast website that replaces the static demo UI.
**Covers:** TL-080, 081, 083, 084 · UX-01–10 · PRIV-05, PRIV-06 (site side).
**Depends on:** Phase 5 (design can start earlier), Phase 8 (integration) · DECISIONS D5, D7, D10.
**Spec:** `UI-UX-SPEC.md` is the source of truth for every screen.

## Tasks
| ID | Task | Detail |
|---|---|---|
| 9.0 | **UI audit of current app** | Screenshot every route at 360, 768, 1280 px; run Lighthouse and axe; keyboard-only walkthrough; list findings as `UX-F-nn` with severity. This replaces guesswork about the current UI (it was not available for this plan) |
| 9.1 | Next 16 conformance | Run `npx @next/codemod@canary middleware-to-proxy .` → `proxy.ts`; confirm route gating still uses `supabase.auth.getUser()` (not `getSession()`); Node ≥ 20.9 via `.nvmrc` and `engines`; build with zero deprecation warnings |
| 9.2 | Design tokens | Implement tokens from the spec once (CSS variables + Tailwind theme). Remove ad-hoc colors/sizes |
| 9.3 | Core components | Button, Input, Field+Error, Card, Badge (verdict), SourceList, Tabs, Dialog, Toast, Skeleton, EmptyState, Banner, Tooltip. Each with all states and keyboard behaviour; Storybook or a `/design` internal route |
| 9.4 | Pages | Landing, How it works, Workbench (Claims / Links / Summarize), Sign up, Sign in, Reset password, Verify email, Dashboard, Account/Privacy, Extension setup, Privacy policy, Terms, Contact, 404, 500, Offline |
| 9.5 | Workbench | Single input with auto-detect (claim text vs URL), explicit tabs as fallback; progress and partial results; per-claim cards with verdict label, plain-language summary, sources (publisher, rating, date, link); "limited check" banner when live checks failed |
| 9.6 | Auth flows | Email verification, password reset, generic error copy, Google OAuth, password rules shown up front, rate-limit messaging, safe `?next=` handling via `getSafeRedirectUrl` retained |
| 9.7 | Dashboard | Real daily usage and caps (D7), extension token create/revoke list, privacy controls, delete account with typed confirmation. Remove quota UI if no caps |
| 9.8 | Content & copy | Apply microcopy table in the spec; reading level ≤ grade 8; no jargon like "NLI" |
| 9.9 | Accessibility | WCAG 2.1 AA: contrast, focus rings, labels, landmarks, live regions for results, reduced motion, 200% zoom, screen reader pass (NVDA + VoiceOver) |
| 9.10 | Performance | Budgets: JS ≤ 170 KB gzipped on landing; fonts ≤ 2 families, `font-display: swap`, self-hosted; images optimized; Lighthouse CI thresholds |
| 9.11 | SEO & meta | Titles, descriptions, OG images, `robots.txt`, sitemap, canonical |
| 9.12 | Security headers | CSP (no `unsafe-inline` if feasible, use nonces), HSTS, frame-ancestors, Referrer-Policy; verify Supabase and API origins in `connect-src` |
| 9.13 | Env separation | Public vs server env vars audited; `SUPABASE_SERVICE_ROLE_KEY` used only in server-only modules (`import 'server-only'`) |
| 9.14 | Retire static demo UI | Remove `static/` from the API; redirect old `/` links |

## Proof tests
Playwright E2E: sign-up → verify email (test inbox) → sign-in → workbench check (mocked API) → create/revoke extension token → delete account · unauthenticated `/dashboard` → `/login?next=…` · `?next=//evil.com` → safe fallback · axe on every route: 0 critical/serious · Lighthouse CI: Perf ≥ 90, A11y ≥ 95, Best-Practices ≥ 95 on landing and workbench · visual regression snapshots at 3 widths · unit tests for components' states · grep test: no `SERVICE_ROLE` in client bundle (`next build` then search `.next/static`).

## Verification
Usability check with 5 non-technical people on the tasks: "check this claim", "check this link", "install and sign in the extension", "delete my account". Record success rate and confusion points. Gate: ≥ 4 of 5 complete each task unaided.

## Exit gate
Every screen in the spec built with all states · axe 0 critical/serious · Lighthouse thresholds met · usability gate met · `proxy.ts` migrated.
