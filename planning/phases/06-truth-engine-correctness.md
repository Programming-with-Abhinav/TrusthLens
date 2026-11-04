# Phase 6 — Truth Engine Correctness [COMPLETED]

**Goal:** never present a wrong or invented verdict; be honest about what the engine does.
**Covers:** TL-020–030 · TRUTH-01–09 · SEC-09 · SUM-01 (partial).
**Depends on:** Phase 5 · DECISIONS D2, D5, D8.
**Status:** Completed. All proof tests green. Rating table golden tests pass with 0 inversions. Parallel verification and source requirement verified.

## Tasks
| ID | Task | Detail | Status |
|---|---|---|---|
| 6.1 | Rating normalization table | Table-driven rating string mapping to verdict enum (`True`, `MostlyTrue`, `Mixed`, `Misleading`, `False`, `Unrated`). Negations prioritized. Unknown returns `Unrated`. 60+ real strings verified | Completed |
| 6.2 | Aggregation rule | Weighted aggregation; conflict between True and False ratings produces `Mixed`. Claim result with no source URL is always `Unverified` | Completed |
| 6.3 | Weak-match guard | Local seed records isolated to demo only; disabled in production; unrelated claims return `Unverified` | Completed |
| 6.4 | Remove `DEMO_DATABASE` | Hardcoded keyword shortcuts removed from production path | Completed |
| 6.5 | Honest naming | Renamed `derive_stance_from_rating`; removed unbacked NLI/cross-encoder claims from comments and docs | Completed |
| 6.6 | Replace trust score | Dropped 0–100 score; calibrated labels and agreement returned | Completed |
| 6.7 | Claim splitting | Handles abbreviations ("Dr.", "U.S.", "e.g.", decimals); preserves ≥ 3-word claims; caps at 5 | Completed |
| 6.8 | Parallel verification | `asyncio.gather` over claims runs verification concurrently | Completed |
| 6.9 | Cache rules | Key = SHA-256 of normalized claim; value stores verdict and sources without input claim text | Completed |
| 6.10 | Synthesis hardening | Untrusted text delimited (`<<< ... >>>`); control characters stripped; output capped ≤ 400 chars | Completed |
| 6.11 | Summarizer limits | Per-user rate limit applied; usage tracked; separate `GEMINI_API_KEY` | Completed |
| 6.12 | Temporal logic | Temporal decay uses UTC and safe math decay formula | Completed |

## Proof tests
All proof tests pass: `test_rating_table_golden` · `test_unrelated_claims_unverified` · `test_verdict_requires_source` · `test_mixed_when_sources_conflict` · `test_claims_run_in_parallel_with_deadline` · `test_split_claims_cases` · `test_injection_samples` · `test_demo_mode_disabled_in_production`.

## Exit gate
Golden sets pass · docs contain no unimplemented capability claims · parallel latency verified with mocks.
