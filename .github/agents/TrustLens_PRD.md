# TrustLens AI – Product Requirements Document (PRD)

**Version:** 1.0 (draft) · **Date:** 10 Oct 2026 · **Sources:** TrustLens Master Spec V5.0 (PDF) and Codebase Specialist file (`trustlens-codebase.agent.md`)

## 1. Summary

TrustLens AI is a browser-based protection layer that does three things in one place: it **checks factual claims** on web pages against fact-check evidence, **scans URLs** for phishing/scam risk, and **summarizes long pages** (Wikipedia, articles, reports) so users can understand and check them quickly. It ships as a Chrome Manifest V3 extension backed by a FastAPI service, plus a small static web UI for demos.

The Master Spec describes a large production vision (Redis, pgvector, NLI model, Gemini synthesis, enterprise console). The current codebase is a **working prototype** with far less. This PRD separates the two: it defines what we have, what the MVP must be, and what comes later.

## 2. Analysis: Spec vs Current Codebase

| Area | Master Spec (target) | Current codebase (verified from the codebase file) | Gap |
|---|---|---|---|
| Claim verification | Hybrid retrieval (pgvector + BM25 + Google Fact Check), cross-encoder NLI, temporal decay, Gemini JSON synthesis | Google Fact Check Tools if `GOOGLE_API_KEY` set; otherwise demo keyword match (`vaccine`, `5g`). Splits text into max 5 claims | Large: no vector DB, NLI, scoring formula, or synthesis |
| URL scanning | Web Risk + WHOIS domain age + SSL entropy + crypto-drainer regex | Google Web Risk if key set; local heuristics (IP host, punycode, hyphens, TLDs, brand look-alikes, keywords, HTTP) | Medium: no domain age, SSL, drainer rules |
| API routes | `POST /api/v1/verify/claim`, `POST /api/v1/scan/url` with rich schemas | `/api/verify` (`{text}` → `claims[]`), `/api/scan` (`{url}` → `level, threats, flags, source`), `/api/health`, `/api/history` | Naming and schema differ; need versioning decision |
| Cache / rate limit / history | Redis L1 cache, token bucket, Postgres audit tables | In-memory, process-local (not persistent, not shared across workers) | Large |
| Extension | Shadow DOM HUD, inline badges, intercept before form submit, `activeTab` only | `content.js` sends selected text to `/api/verify`; `popup.js` scans active tab via `/api/scan`; hardcoded `http://localhost:8000` | Large: no inline HUD or navigation interceptor |
| Page summarizer | **Not covered anywhere in the spec** | Not implemented | New feature: see section 8.5 |
| Web UI | Not a focus | Static `index.html`, `app.js`, `interactions.js`, `style.css` served at `/` | Fine for demo |
| Tests / deploy | pytest >85% coverage, Playwright, K8s | `test_main.py` smoke tests; Dockerfile + docker-compose | Medium |

**Key finding:** the spec's section 10 lists Redis, pgvector, Shadow DOM and rate limiting under "Currently Implemented (MVP)". The codebase file does not support that (in-memory only, no HUD described). Treat those as *planned*, and correct the spec before showing it to judges, investors or mentors.

## 3. Issues Found in the Spec (fix before reuse)

1. **ROI formula (section 13):** $539,810 / $96,000 = 562% is *benefit ÷ cost*. True ROI is (benefit − cost) ÷ cost ≈ **462%**. Label it correctly.
2. **Enterprise LTV (section 14):** "$4,800 (60-seat avg, 24 mo)" does not match $8 × 60 seats × 24 months = $11,520. Either the seat count, lifetime, or LTV figure is wrong, and the LTV:CAC ratio (5.64:1) depends on it.
3. **"Zero hallucination" / "zero credential breaches" claims:** these are guarantees no system can make. The spec itself cites 8–22% hallucination for raw LLMs; grounding reduces but does not eliminate errors. Reword to "grounded in retrieved sources, with citations".
4. **Unsourced statistics:** $78B fraud cost, 88% abandonment, 72% spear-phishing with fake-news narratives, "85% time reduction". Add citations or mark as assumptions. The MIT finding (false news spreads faster than true) is real research; check the exact multiplier you quote.
5. **Latency target (<1.6 s)** with retrieval + cross-encoder + Gemini on a cold path is aggressive; treat as a goal to benchmark, not a promise.
6. **Google Custom Search deprecation notice (section 26):** verify the dates against Google's current documentation before presenting as fact.
7. **Missing feature:** the spec does not cover summarizing Wikipedia or other long text. This PRD adds it (FR-S1 to FR-S10) and the spec should be updated to match.
8. **Scope vs timeline:** the 12-day sprint plan covers a full stack (K8s, SOC 2 prep, ONNX). Not realistic for one student team; the phasing below fixes this.

## 4. Problem Statement

People make decisions from unverified claims and are targeted by scam links, often together (a fake-news style message that carries a phishing link). Existing tools split the problem: fact-checkers ignore malicious URLs; security tools ignore false text. Verification also requires leaving the page, so people skip it.

## 5. Goals and Non-Goals

**Goals (MVP)**
- G1: Let a user check a selected claim without leaving the page and see a clear, sourced rating.
- G2: Let a user scan the current page/link and get a risk level with plain-language reasons.
- G3: Be honest about confidence: always show source and whether the result is demo, heuristic or API-backed.
- G4: Stay usable with no API key (demo mode).
- G5: Let a user summarize a long page (Wikipedia, article, report) in one click and, optionally, see which key points are fact-checked.

**Non-goals (MVP)**
- Enterprise SecOps console, SSO/SCIM, billing, SOC 2.
- Speech-to-text, edge ONNX, multi-region Kubernetes.
- Claiming authoritative truth or guaranteed URL safety.

## 6. Target Users

| Persona | Need | MVP priority |
|---|---|---|
| Everyday user / student (primary for MVP) | Quick check on a claim or suspicious link | High |
| Retail investor / crypto trader (Sarah) | Spot fake announcements and drainer links | Medium |
| Newsroom editor (Marcus) | Match against prior debunks | Later |
| Enterprise CISO (Elena) | Block credential-harvesting pages, audit logs | Later |

Recommendation: **validate with consumers and students first**; the enterprise story needs infrastructure the prototype does not have.

## 7. Product Scope by Phase

| Phase | Theme | Contents |
|---|---|---|
| **P0 – Current prototype** | Demo works | Everything in section 2 "current" column |
| **P1 – Solid MVP** | Trustworthy and testable | **Page summarizer (extractive demo mode + LLM mode)**, better claim extraction, stable API contract, persistent cache/history, improved extension UI, configurable backend URL, expanded tests, documented limits |
| **P2 – Intelligence** | Evidence quality | Embedding retrieval over ClaimReview data, NLI stance scoring, source weighting, temporal decay, optional LLM summary strictly grounded in retrieved evidence, fact-check badges on summary key points |
| **P3 – Protect** | Active defense | Navigation interceptor, domain age/SSL signals, drainer rules, Shadow DOM inline badges |
| **P4 – Business** | Commercial | Accounts, quotas, billing, admin console, audit API |

## 8. Functional Requirements

### 8.1 Claim Verification

| ID | Requirement | Phase |
|---|---|---|
| FR-C1 | Accept `{text}` and return a `claims[]` array (existing contract preserved) | P0 |
| FR-C2 | Split input into at most 5 sentence-like claims; short input becomes one claim | P0 |
| FR-C3 | With API key: query Google Fact Check Tools; without: demo keyword fallback, clearly labelled as demo | P0 |
| FR-C4 | Each claim result shows rating, source/publisher, link, and a `source` field (`demo`, `google`, etc.) | P1 |
| FR-C5 | Return "no evidence found" explicitly rather than a guessed verdict | P1 |
| FR-C6 | Atomic claim extraction (skip opinions, questions, boilerplate) | P1/P2 |
| FR-C7 | Retrieval over embedded ClaimReview records (vector + keyword, rank fusion) | P2 |
| FR-C8 | NLI stance scoring and composite truth score with source weights and time decay | P2 |
| FR-C9 | Optional LLM synthesis constrained to retrieved documents, with citations; falls back to raw ClaimReview if disabled | P2 |

### 8.2 URL Scanning

| ID | Requirement | Phase |
|---|---|---|
| FR-U1 | Accept `{url}` and return `level`, `threats`, `flags`, `source` (existing contract preserved) | P0 |
| FR-U2 | Local heuristics: IP host, punycode, hyphens, selected TLDs, brand look-alikes, suspicious keywords, HTTP | P0 |
| FR-U3 | With API key: Google Web Risk lookup merged with heuristics | P0 |
| FR-U4 | Validate and normalise URLs; reject malformed input with a clear error | P1 |
| FR-U5 | Human-readable explanation for every flag | P1 |
| FR-U6 | Domain age and SSL signals | P3 |
| FR-U7 | Crypto-drainer pattern rules for wallet-connect pages | P3 |
| FR-U8 | Block/warn interstitial before credential entry, only above a high confidence threshold | P3 |

### 8.3 Extension (Chrome MV3)

| ID | Requirement | Phase |
|---|---|---|
| FR-E1 | Selected text is sent to verify; result shown to user | P0 |
| FR-E2 | Popup scans the active tab URL | P0 |
| FR-E3 | Backend URL is configurable (options page), not hardcoded to localhost | P1 |
| FR-E4 | Result card rendered with safe DOM APIs only (`textContent`, `createElement`) | P1 |
| FR-E5 | Minimal permissions (`activeTab` where possible) | P1 |
| FR-E6 | Shadow DOM overlay so page CSS cannot spoof or break the UI | P3 |
| FR-E7 | Inline badges on detected claims | P3 |

### 8.4 Web Interface

| ID | Requirement | Phase |
|---|---|---|
| FR-W1 | Claim and URL forms with validation and loading states | P0 |
| FR-W2 | Render results without unsafe HTML interpolation | P0 |
| FR-W3 | Show recent history | P0 (in-memory) |
| FR-W4 | Visible "demo mode" indicator when no API key is configured | P1 |

### 8.5 Summarizer (new)

| ID | Requirement | Phase |
|---|---|---|
| FR-S1 | `POST /api/summarize` accepts `{ "text": string, "url": string (optional), "length": "short" or "medium" }` and returns `summary`, `key_points[]`, `truncated` (bool) and `source` (`extractive` or `llm`) | P1 |
| FR-S2 | Extension extracts main content (selection if present, otherwise article body), stripping menus, ads, and hidden or zero-size elements | P1 |
| FR-S3 | Long input is split into chunks, each chunk summarized, then merged (map-reduce) to fit model limits; response states when input was truncated | P1 |
| FR-S4 | Wikipedia pages are summarized section by section with an optional "key facts" list; a pasted Wikipedia link may be fetched through the MediaWiki API | P1 |
| FR-S5 | Summary uses only the supplied text (no outside facts) and is labelled "AI summary, may omit details" with a link to the original | P1 |
| FR-S6 | Demo mode (no API key) uses extractive summarization (top-ranked sentences) so the feature works offline | P1 |
| FR-S7 | Summary shown in popup or side panel via safe DOM APIs only, with copy button and length control | P1 |
| FR-S8 | Summarization runs only when the user clicks; never automatic on page load | P1 |
| FR-S9 | Cache by text hash; apply the same rate limiting as other endpoints | P1 |
| FR-S10 | Optionally verify the top 3-5 key points with the claim pipeline and show a trust badge on each; run the URL scan on the source page and show its risk level beside the summary | P2 |

### 8.6 Platform

| ID | Requirement | Phase |
|---|---|---|
| FR-P1 | `/api/health` endpoint | P0 |
| FR-P2 | Rate limiting (process-local today) | P0 |
| FR-P3 | Persistent cache and history (SQLite or Postgres; Redis for shared rate limiting if multi-worker) | P1 |
| FR-P4 | Decide on API versioning (`/api/v1/...` per spec) with a compatibility alias for current routes | P1 |
| FR-P5 | Structured logs without raw user browsing data | P1 |

## 9. API Contract

**Current (preserve in P1):**

- `POST /api/verify` – request `{ "text": string }` → `{ "claims": [ ... ] }`
- `POST /api/scan` – request `{ "url": string }` → `{ "level", "threats", "flags", "source" }`
- `GET /api/health`, `GET /api/history`
- **New:** `POST /api/summarize` - request `{ "text": string, "url"?: string, "length"?: "short"|"medium" }` → `{ "summary", "key_points", "truncated", "source" }`

**Target (P2+), from the spec:** `/api/v1/verify/claim` returning `claim_id`, `verdict`, `trust_score`, `evidence[]`, `reasoning`; `/api/v1/scan/url` returning `is_threat`, `threat_type`, `should_block`, `domain_age_days`, `mitigation`. Add new fields as optional additions rather than renaming existing ones, so the extension and web UI keep working.

## 10. Non-Functional Requirements

- **Performance:** target p95 under 2 s for API-backed checks and under 100 ms for cache hits in P1; measure before promising the spec's 1.6 s cold path.
- **Reliability:** if Google APIs fail or quota runs out, fall back to heuristics/demo and say so in the response.
- **Security:** treat claims, URLs, API output and history as untrusted. No unsafe HTML. Strip hidden-text content before any LLM use. Keep secrets in environment variables.
- **Privacy:** send only selected text or URL (summarization sends full page text, so it is user-triggered only and documented clearly); avoid storing identifiable browsing history; document what is logged (aligns with the spec's DPDP/GDPR intent).
- **Honesty:** the UI must never present heuristics as authoritative verification or a safety guarantee.
- **Compatibility:** Chromium browsers via MV3.

## 11. Architecture

**Today:** Extension / static UI → FastAPI (`main.py`) → Google Fact Check + Web Risk (optional) → in-memory cache, history, rate limiter.

**Target:** Extension → FastAPI gateway (rate limit, validation) → Truth engine (retrieval + NLI + scoring) and Safety engine (Web Risk + heuristics) → Postgres/pgvector + Redis, with optional grounded LLM synthesis.

**Suggested refactor (P1):** split `main.py` into modules (`routes`, `claims`, `url_scan`, `cache`, `config`) so the P2 truth engine and P3 safety engine have clear homes. Keep the vanilla JS and static-file approach; add no frontend framework without a concrete need.

## 12. Success Metrics

| Metric | Target (proposed) | How measured |
|---|---|---|
| Claim check completes with a result or explicit "no evidence" | 100% | API tests |
| URL scan precision on a labelled test set (phishing vs safe) | Define set of 100+ URLs; set target after baseline | Offline evaluation |
| False-positive rate on popular safe sites | Under 2% | Same test set |
| p95 latency, cache hit / miss | Measured and reported | Logs |
| Summary usefulness: testers rate summaries as accurate and complete | ≥70% positive on a 20-page sample (Wikipedia + news) | Manual review + survey |
| Pilot usability | 20–50 testers; ≥60% say result was clear and useful | Survey |
| Weekly repeat usage among testers | Track first, set threshold after | Opt-in counter |

The spec's 40% WAU/MAU, 0.05% crash rate and Sean Ellis thresholds are reasonable later-stage goals but need an installed user base to measure.

## 13. Testing and Validation

- `pytest` from repo root for backend; extend `test_main.py` with: invalid inputs, 5-claim cap, demo fallback labelling, each URL heuristic, API-failure fallback, rate limit behavior, response-shape stability.
- Summarizer: tests for empty/very long input, chunking and truncation flag, extractive fallback without API key, hidden-text stripping, cache hit, and a manual faithfulness check (no invented facts) on 20 pages.
- Extension: manual checklist on 10–20 real pages (news, social, webmail) for no layout breakage; later Playwright.
- Docker: validate via existing Compose setup.
- Security: XSS test strings in claims/URLs; prompt-injection test set before any LLM is added.

## 14. Milestones (realistic, replace the 12-day plan)

| Milestone | Duration (suggested) | Exit criteria |
|---|---|---|
| M1 – Harden prototype (P1 part 1) | 1–2 weeks | Stable contract, tests green, configurable backend URL, demo-mode labelling |
| M2 – Persistence and UX (P1 part 2) | 2–3 weeks | Persistent cache/history, result card in extension, URL validation, working summarizer (extractive + LLM) in extension popup |
| M3 – Evidence engine (P2) | 3–5 weeks | Seeded ClaimReview set, retrieval working, scoring evaluated on a small labelled set |
| M4 – Active protection (P3) | 3–4 weeks | Domain age/SSL signals, interstitial with high threshold, Shadow DOM overlay |
| M5 – Pilot | 2 weeks | 20–50 users, survey and metrics review |

Business phases (billing, enterprise pilots) start only after M5 results.

## 15. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Google API quota or key unavailable | Medium | High | Caching, heuristic fallback, clear "source" labelling |
| Fact Check API has no result for most claims | High | High | Explicit "no evidence"; P2 retrieval; set user expectations |
| False positives on safe sites | Medium | High | High threshold for any blocking; warn-only in early phases |
| LLM hallucination or prompt injection (P2) | Medium | High | Ground only on retrieved text, sanitise input, fallback to raw evidence |
| Scope too large for the team | High | High | Phase plan; ship P1 before P2 |
| Chrome Web Store rejection | Medium | Medium | Minimal permissions, privacy policy |
| In-memory state lost on restart / multi-worker inconsistency | High (today) | Medium | P1 persistence |
| Summaries omit nuance or add facts not in the source | Medium | Medium | Source-only prompts, "may omit details" label, link to original, faithfulness review |
| Full page text sent to backend raises privacy concern | Medium | Medium | User-triggered only, documented, no raw text stored beyond cache hash |
| Overclaiming accuracy in pitch | Medium | High | Fix spec wording (section 3) |

## 16. Open Questions

1. Is the main audience for the next milestone a demo/hackathon, a college submission, or a real launch? This decides how much of P2–P4 matters.
2. Will you adopt the `/api/v1/...` routes from the spec, or keep `/api/...`?
3. Do you have a Google API key and quota for Fact Check Tools and Web Risk?
4. Which database for P1 persistence: SQLite (simplest) or Postgres (matches the spec)?
5. Who owns each module (spec's RACI assumes four roles)? Is the team smaller?
6. Do you have a labelled dataset for claims and URLs to evaluate quality?
7. Summarizer: extractive-only for the first release, or LLM (Gemini) from the start? Should Wikipedia links be fetched by the backend?

## 17. Immediate Next Steps

1. Correct the spec issues listed in section 3.
2. Decide the open questions above (especially 1, 2 and 4).
3. Start M1: stabilise the contract and expand `test_main.py`.
4. Build a small labelled URL/claim test set so improvements can be measured.
5. Add the summarizer to M2 and start with the extractive demo mode.
