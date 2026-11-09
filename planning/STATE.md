# STATE — honest status (update in every PR)

**Milestone:** v1.1 Production Readiness · **Last updated:** 2026-11-04 · **Phase:** 5, 6, 7 Complete (Phase 8 API hardening next)

## Where the project really is
- **Phase 5 (Baseline, Security & Privacy):** Complete. 11/11 proof tests green. Unseen code audited in `audits/PHASE-5-CODE-AUDIT.md`. No raw user claims/URLs in logs, DB, or cache. Fail-closed auth and rate limiting active.
- **Phase 6 (Truth Engine Correctness):** Complete. Table-driven rating mapper with 60+ ratings; source-free claims return `Unverified`; conflicting sources return `Mixed`; parallel `asyncio.gather` claim verification; honest naming.
- **Phase 7 (URL Scanner Accuracy & Safety):** Complete. SSRF protection for IPv4/IPv6/metadata/loopback; official brand domains protected; lookalikes and crypto-drainers flagged; top domains never marked Dangerous.
- **Frontend & Full Stack:** Next.js 16.4.3 production build passes; ESLint passes with 0 errors.

## Phase status
| Phase | Status | Evidence |
|---|---|---|
| 5 Baseline, security & privacy | Complete | 46 backend tests pass (11 Phase 5 proof tests all passing); Next.js 16.4.3 production build passes; ESLint 0 errors; code audit in `audits/PHASE-5-CODE-AUDIT.md` |
| 6 Truth engine | Complete | All Phase 6 proof tests pass (`test_rating_table_golden`, `test_unrelated_claims_unverified`, `test_verdict_requires_source`, `test_mixed_when_sources_conflict`, `test_claims_run_in_parallel_with_deadline`, `test_split_claims_cases`, `test_injection_samples`, `test_demo_mode_disabled_in_production`) |
| 7 URL scanner | Complete | All Phase 7 proof tests pass (`test_top1000_domains_never_dangerous`, `test_brand_official_domains_not_flagged`, `test_brand_lookalikes_flagged`, `test_ssrf_targets_blocked`, `test_non_http_schemes_rejected`, `test_unknown_rdap_never_blocks`, `test_score_table`, `test_concurrent_scans_do_not_block`) |
| 8 API hardening | In progress | Routing parity, error shape normalization, liveness/readiness, pydantic settings |
| 9 Web UI/UX | Not started | — |
| 10 Extension & Store | Not started | — |
| 11 QA & release | Not started | — |

## Defect register progress
Total tracked: see `00-PROJECT-ANALYSIS.md` §4.
- **Closed:** TL-001, TL-002, TL-003, TL-004, TL-005, TL-006, TL-007, TL-008, TL-009, TL-010, TL-011, TL-020, TL-021, TL-022, TL-023, TL-024, TL-026, TL-027, TL-028, TL-030, TL-040, TL-041, TL-042, TL-043, TL-044, TL-046, TL-057, TL-058.
- **Open for Phase 8+:** TL-050, TL-051, TL-052, TL-053, TL-054, TL-055, TL-056.

## Evidence log (append only)
| Date | Item (TL-/REQ-) | Evidence (test name, CI run URL, screenshot path) | Verified by |
|---|---|---|---|
| 2026-10-24 | TL-090/TL-098 | Stage 0: `xyz123` returns `Unverified`; Next.js upgraded from 16.4.0 to 16.4.3 and production build passes | Coding agent |
| 2026-10-24 | TL-001/002/003/004/006/007/009/011/057 | Phase 5 partial: 32 backend tests pass; cache excludes claim text; demo keyword fallback removed; non-http URL schemes rejected; usage writes use the atomic Supabase RPC; static/extension mounts gate on production mode | Coding agent |
| 2026-10-25 | TL-021 | `test_map_verdict_handles_negation_and_unknown_ratings` passes; verdict mapping now treats partial truths as `Mixed`, negated claims as `False`, and unrecognized ratings as `Unrated` | Coding agent |
| 2026-10-25 | TL-058 | `test_production_requires_runtime_config` passes; production mode now fails closed without the required API, Supabase, and CORS config keys | Coding agent |
| 2026-11-04 | Phase 5 Exit Gate | All 11 proof tests pass (`test_history_never_contains_input`, `test_history_requires_auth_or_absent`, `test_cache_values_exclude_claim_text`, `test_forged_jwt_rejected_in_all_modes`, `test_expired_jwt_rejected`, `test_supabase_outage_returns_503_not_trust`, `test_authenticated_users_are_rate_limited`, `test_cors_rejects_unknown_origin`, `test_no_key_reuse`, `test_oversize_input_rejected`, `test_logs_contain_no_user_content`). Total 46 tests green. Next.js 16 build + ESLint green. | Coding agent |
| 2026-11-04 | Phase 6 Exit Gate | 8/8 proof tests pass (`test_rating_table_golden`, `test_unrelated_claims_unverified`, `test_verdict_requires_source`, `test_mixed_when_sources_conflict`, `test_claims_run_in_parallel_with_deadline`, `test_split_claims_cases`, `test_injection_samples`, `test_demo_mode_disabled_in_production`). Parallel verification active; honest naming applied. Total 54 tests green. | Coding agent |
| 2026-11-04 | Phase 7 Exit Gate | 8/8 proof tests pass (`test_top1000_domains_never_dangerous`, `test_brand_official_domains_not_flagged`, `test_brand_lookalikes_flagged`, `test_ssrf_targets_blocked`, `test_non_http_schemes_rejected`, `test_unknown_rdap_never_blocks`, `test_score_table`, `test_concurrent_scans_do_not_block`). Total 62 tests green. | Coding agent |
| 2026-11-08 | Frontend CI Build | Fixed TypeScript type mismatch with centralized `lib/types.ts`; `npx tsc --noEmit`, `npm run lint`, and `npm run build` all pass cleanly with 0 errors; aligned CI workflow path to `my-app` | Coding agent |
| 2026-11-09 | TL-053/TL-054 | Phase 8 Step 1: `test_legacy_and_v1_route_parity` and `test_no_static_mounts_in_prod` pass. Unified APIRouter mounted at /api/v1 and legacy /api with Deprecation header; static mounts and docs disabled in production. Total 64 tests green. | Coding agent |
| 2026-11-09 | TL-056/API-06/07/08 | Phase 8 Step 2: `test_error_contract_has_request_id`, `test_security_headers_present`, and `test_readyz_degrades_when_redis_down` pass. Uniform error envelope, security headers (nosniff, HSTS, referrer-policy, private cache-control), and cached readiness probe verified. Total 67 tests green. | Coding agent |
| 2026-11-09 | TL-058/8.1/8.4/8.3/8.15/8.11/8.12 | Phase 8 Steps 3-5: `test_prod_refuses_to_boot_without_config`, `test_summaries_are_counted`, `test_usage_increment_is_atomic`, `test_rate_limit_shared_across_workers` pass. record_summary added to supabase_client; budget guard constants (DAILY_FREE_*_LIMIT) added; Dockerfile upgraded to multi-stage build with non-root user and HEALTHCHECK; requirements.txt/requirements-dev.txt split. Total 71 tests green. | Coding agent |

## Open decisions
D1–D10 in `DECISIONS.md` — none resolved.

## Known unknowns
Unseen code audit completed (see `audits/PHASE-5-CODE-AUDIT.md`). Static UI isolated to non-production mode. Next.js server actions audited for safe service role isolation.
