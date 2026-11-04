# Phase 6 — Truth Engine Correctness

**Goal:** never present a wrong or invented verdict; be honest about what the engine does.
**Covers:** TL-020–030 · TRUTH-01–09 · SEC-09 · SUM-01 (partial).
**Depends on:** Phase 5 · DECISIONS D2, D5, D8.

## Tasks
| ID | Task | Detail |
|---|---|---|
| 6.1 | Rating normalization table | Replace `map_verdict` regexes with a lookup of normalized rating strings → verdict enum (`True`, `MostlyTrue`, `Mixed`, `Misleading`, `False`, `Unrated`). Handle negations ("not true", "inaccurate", "no evidence", "unproven", "satire", "outdated", "missing context"). Unknown → `Unrated` (never `Mixed`). Collect ≥ 60 real strings from Fact Check API responses across publishers |
| 6.2 | Aggregation rule | Majority across publishers weighted by publisher; if conflict (True and False both present) → `Mixed` with sources shown. Require ≥ 1 source URL for any verdict |
| 6.3 | Weak-match guard | If keeping the local seed (demo only): require claim↔record similarity above a threshold calibrated on a labelled set of related/unrelated pairs; below → `Unverified`. Tag results `source: "demo"`; disabled when `ENV=production` |
| 6.4 | Remove `DEMO_DATABASE` | Delete the keyword → verdict shortcut (`vaccine`, `5g`) from the production path |
| 6.5 | Honest naming | Rename `classify_nli_stance` → `derive_stance_from_rating` (or delete the field); remove "NLI", "dense vector", "cross-encoder" wording from code comments, API docs, UI, README. If D2 chooses real NLI, implement it as a separate milestone |
| 6.6 | Replace trust score | Return `{verdict, evidence_count, agreement, newest_review_date, sources[]}`; drop the 0–100 number and `confidence` (or compute `agreement` = share of sources agreeing, labelled as such) |
| 6.7 | Claim splitting | Keep ≥ 3-word claims; use a proper sentence splitter (handle "Dr.", "U.S.", decimals); cap total input; never silently drop all content |
| 6.8 | Parallel verification | `asyncio.gather` over claims with a per-upstream timeout (≤ 4 s) and overall deadline (≤ 6 s); return `partial: true` with per-claim status if a claim times out |
| 6.9 | Cache rules | Normalize (case, whitespace, punctuation); key = SHA-256(norm claim + mode); TTL 24 h (found) / 1 h (not found); no claim text in value |
| 6.10 | Synthesis hardening | Treat claim and evidence as untrusted: strip control chars, wrap in delimiters, cap lengths; instruct model to quote only provided evidence; validate output (length ≤ 400 chars, no URLs not in sources); `maxOutputTokens` ≥ 256; fall back to deterministic text |
| 6.11 | Summarizer limits | Per-user daily cap; separate `GEMINI_API_KEY`; count usage |
| 6.12 | Temporal logic | If recency weighting is kept: fix constant/docs, use UTC; otherwise remove |

## Proof tests
`test_rating_table_golden` (≥ 60 strings; includes every inversion case) · `test_unrelated_claims_unverified` (50 claims incl. true statements about water, vaccines safety testing, 5G spectrum auctions) · `test_verdict_requires_source` · `test_mixed_when_sources_conflict` · `test_cache_ttl_and_mode_isolation` · `test_claims_run_in_parallel_with_deadline` (mock upstream sleeps; total < deadline) · `test_split_claims_cases` · `test_injection_samples` (claims/evidence containing "ignore previous instructions", markup, URLs) · `test_demo_mode_disabled_in_production`.

## Verification
Run the 50-claim golden set against a staging deployment **with a real Fact Check key**; a second reviewer reads 20 random outputs against the cited fact-check pages and records agreement. Target: 0 inversions, ≥ 95% rating agreement.

## Exit gate
Golden sets pass · docs contain no unimplemented capability claims · latency test passes with mocked slow upstreams.
