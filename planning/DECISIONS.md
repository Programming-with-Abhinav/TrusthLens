# Owner Decisions (resolve before the blocked phase starts)

Each decision has a **recommended default**. If the owner does not answer by the "needed by" gate, the developer proceeds with the default and records it here.

| # | Decision | Options | Recommended default | Blocks |
|---|---|---|---|---|
| D1 | **Hosting & domains** | (a) Next.js on Vercel + API container on Cloud Run/Fly/Render; (b) everything on one VPS with Docker + Caddy; (c) other | (a), two subdomains: `trustlens.<domain>` (site) and `api.trustlens.<domain>` (API) | Phase 8 |
| D2 | **Truth data strategy** | (a) Google Fact Check API is the only source of verdicts; local seed removed from user results; (b) keep local corpus but build real ingestion + embeddings now | (a). Build real semantic retrieval as a later milestone (v1.2) | Phase 6 |
| D3 | **Storage** | (a) Redis (cache, rate limits) + Supabase Postgres (accounts, usage), **no history table**; (b) keep SQLite single-instance | (a). SQLite is fine only for local dev | Phase 5/8 |
| D4 | **Pre-navigation scanning privacy model** | (a) Local heuristics only until a page looks risky, then ask the API; (b) send every visited URL to the API; (c) opt-in "Protection mode" | (a) default, (c) as opt-in. Never (b) silently — it contradicts "privacy-first" | Phase 10 |
| D5 | **Verdict display** | (a) Labels: True / Mostly true / Mixed / Misleading / False / Unverified with source list; no numeric score; (b) keep 0–100 "trust score" | (a). A 0–100 score implies precision the data does not have | Phase 6/9 |
| D6 | **Extension sign-in** | (a) Revocable extension API tokens created in the dashboard; (b) `externally_connectable` handoff from the website; (c) paste Supabase session token | (a) now. (c) is removed: tokens expire and are powerful | Phase 10 |
| D7 | **Plans and limits** | (a) Free only for v1.1 with per-user daily caps to control cost; (b) Free + Pro with Stripe | (a). Stripe moves to v1.2. Dashboard shows real caps | Phase 8/9 |
| D8 | **LLM use** | (a) Gemini for summaries and claim explanations with spend cap + extractive fallback; (b) extractive only | (a) with a hard monthly budget alert and a separate key | Phase 6/8 |
| D9 | **Legal & compliance** | Privacy policy, Terms, disclaimer ("not a guarantee of truth or safety"), data-deletion path, contact address. Applicable laws (e.g. India's DPDP Act 2023, GDPR for EU users) | Have counsel review before Store submission. This plan is not legal advice | Phase 10/11 |
| D10 | **Brand & design direction** | Approve the proposal in `UI-UX-SPEC.md` §2. Fix the "TrusthLens" typo (README title, repo folder name) | Approve proposal or supply brand assets | Phase 9 |

## Decision log
| # | Date | Decision taken | By |
|---|---|---|---|
| | | | |
