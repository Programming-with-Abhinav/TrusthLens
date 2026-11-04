# STATE — honest status (update in every PR)

**Milestone:** v1.1 Production Readiness · **Last updated:** 2026-11-04 · **Phase:** 5 Complete (Phases 6 & 7 in progress)

## Where the project really is
Baseline security, privacy protections, and fail-closed authentication are fully locked and verified in Phase 5. No raw user claims or URLs are stored or logged. Auth fails closed on token manipulation or upstream outages. Truth engine and URL scanner refinements are in progress.

## Phase status
| Phase | Status | Evidence |
|---|---|---|
| 5 Baseline, security & privacy | Complete | 46 backend tests pass (11 Phase 5 proof tests all passing); Next.js 16.4.3 production build passes; ESLint 0 errors; code audit in `audits/PHASE-5-CODE-AUDIT.md` |
| 6 Truth engine | In progress | Source-free claims return Unverified; seed corpus removed from live verdicts; no trust_score field |
| 7 URL scanner | In progress | HTTP(S) and userinfo enforcement; private/loopback/link-local/metadata/IPv6 SSRF rejection; official-brand-domain guards |
| 8 API hardening | Not started | — |
| 9 Web UI/UX | Not started | — |
| 10 Extension & Store | Not started | — |
| 11 QA & release | Not started | — |

## Defect register progress
Total tracked: see `00-PROJECT-ANALYSIS.md` §4. Closed: TL-001, TL-002, TL-003, TL-004, TL-005, TL-006, TL-007, TL-008, TL-009, TL-011, TL-057. Critical open: TL-020, TL-021 (partially addressed in Phase 6).

## Evidence log (append only)
| Date | Item (TL-/REQ-) | Evidence (test name, CI run URL, screenshot path) | Verified by |
|---|---|---|---|
| 2026-10-24 | TL-090/TL-098 | Stage 0: `xyz123` returns `Unverified`; Next.js upgraded from 16.4.0 to 16.4.3 and production build passes | Coding agent |
| 2026-10-24 | TL-001/002/003/004/006/007/009/011/057 | Phase 5 partial: 32 backend tests pass; cache excludes claim text; demo keyword fallback removed; non-http URL schemes rejected; usage writes use the atomic Supabase RPC; static/extension mounts gate on production mode | Coding agent |
| 2026-10-25 | TL-021 | `test_map_verdict_handles_negation_and_unknown_ratings` passes; verdict mapping now treats partial truths as `Mixed`, negated claims as `False`, and unrecognized ratings as `Unrated` | Coding agent |
| 2026-10-25 | TL-058 | `test_production_requires_runtime_config` passes; production mode now fails closed without the required API, Supabase, and CORS config keys | Coding agent |
| 2026-11-04 | Phase 5 Exit Gate | All 11 proof tests pass (`test_history_never_contains_input`, `test_history_requires_auth_or_absent`, `test_cache_values_exclude_claim_text`, `test_forged_jwt_rejected_in_all_modes`, `test_expired_jwt_rejected`, `test_supabase_outage_returns_503_not_trust`, `test_authenticated_users_are_rate_limited`, `test_cors_rejects_unknown_origin`, `test_no_key_reuse`, `test_oversize_input_rejected`, `test_logs_contain_no_user_content`). Total 46 tests green. Next.js 16 build + ESLint green. | Coding agent |

## Open decisions
D1–D10 in `DECISIONS.md` — none resolved.

## Known unknowns
Unseen code audit completed (see `audits/PHASE-5-CODE-AUDIT.md`). Static UI isolated to non-production mode. Next.js server actions audited for safe service role isolation.
