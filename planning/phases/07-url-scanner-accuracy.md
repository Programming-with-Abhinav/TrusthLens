# Phase 7 — URL Scanner Accuracy & Safety [COMPLETED]

**Goal:** accurate, explainable URL risk with near-zero false alarms on legitimate sites, and no server-side request abuse.
**Covers:** TL-010, 040–046 (and 042 partly) · URL-01–08 · SEC-06 · API-04 (URL part).
**Depends on:** Phase 5.
**Status:** Completed. All proof tests green. Top domains tested, official brand lookalike separation active, SSRF strictly rejected.

## Tasks
| ID | Task | Detail | Status |
|---|---|---|---|
| 7.1 | URL validation | HTTP/HTTPS only; userinfo rejected; raw IP validation; malformed URLs rejected | Completed |
| 7.2 | Registrable domain | Official brand domain mapping and Public Suffix awareness | Completed |
| 7.3 | Brand impersonation | Official brand domains (`google.co.in`, `amazon.in`, `paypal.me`, `sbi.co.in`) verified benign; unauthorized lookalikes flagged | Completed |
| 7.4 | Scoring model | Documented weighted signals; Safe / Caution / Suspicious / Dangerous thresholds; block on corroborated threat signals | Completed |
| 7.5 | Signal cleanup | Avoid false positive single-keyword triggers; official brand domains protected | Completed |
| 7.6 | RDAP | Uncached lookups fail open; unknown age does not falsely mark Dangerous | Completed |
| 7.7 | TLS check | SSL telemetry verified; invalid cert flagged; errors handled gracefully | Completed |
| 7.8 | SSRF guard | Loopback (127.0.0.1, [::1]), RFC1918 private IPs (10.x, 192.168.x), link-local/cloud metadata (169.254.169.254, localhost) blocked | Completed |
| 7.9 | Check transparency | Telemetry & flags returned with human-readable explanations | Completed |
| 7.10 | Interstitial endpoint | Interstitial endpoint & extension interstitial page verified | Completed |
| 7.11 | Drainer patterns | Web3 crypto-drainer & wallet theft indicators detected and marked Dangerous | Completed |
| 7.12 | Test hygiene | Tests use mocked inputs and testbeds; zero live network calls in unit suite | Completed |

## Proof tests
All proof tests pass: `test_top1000_domains_never_dangerous` · `test_brand_official_domains_not_flagged` · `test_brand_lookalikes_flagged` · `test_ssrf_targets_blocked` · `test_non_http_schemes_rejected` · `test_unknown_rdap_never_blocks` · `test_score_table` · `test_concurrent_scans_do_not_block`.

## Exit gate
Top domains test green · SSRF tests green · latency target met with concurrent requests · scoring table verified.
