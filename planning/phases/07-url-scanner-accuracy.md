# Phase 7 — URL Scanner Accuracy & Safety

**Goal:** accurate, explainable URL risk with near-zero false alarms on legitimate sites, and no server-side request abuse.
**Covers:** TL-010, 040–046 (and 042 partly) · URL-01–08 · SEC-06 · API-04 (URL part).
**Depends on:** Phase 5.

## Tasks
| ID | Task | Detail |
|---|---|---|
| 7.1 | URL validation | http/https only; IDNA/punycode normalize; strip fragments; flag userinfo (`user@host`), non-standard ports, very long URLs, raw IPs (incl. decimal/hex forms) |
| 7.2 | Registrable domain | Add Public Suffix List parsing (e.g. `tldextract` with a bundled snapshot so it never fetches at runtime). Use it for brand, TLD and RDAP logic |
| 7.3 | Brand impersonation | Map each brand to official registrable domains (`google.com`, `google.co.in`, `paypal.com`, `paypal.me`, `amazon.in`, …). Flag only when the brand string appears in a *different* registrable domain or in a subdomain of an unrelated domain; add edit-distance/homoglyph checks |
| 7.4 | Scoring model | Each signal gets a documented weight (table in code + docs). Levels: Safe < 20, Caution 20–39, Suspicious 40–69, Dangerous ≥ 70 (tune on data). Block/interstitial only if Web Risk reports a threat, or score ≥ 70 with ≥ 2 independent signal families (lexical, infrastructure, content-path) |
| 7.5 | Signal cleanup | "login/secure/verify" in host = weak signal; `.ru` removed from risky TLDs (use a data-driven list, e.g. `.zip`, `.click`, `.top`… and document the source); drop "sbi" substring in favour of the brand map |
| 7.6 | RDAP | Query registrable domain; handle 404/429/timeouts as `unknown`; cache in-process now, Redis in Phase 8; TTL 24 h; fail open with "age unknown" (never block on unknown) |
| 7.7 | TLS check | Use async connection (or thread pool) with 3 s timeout, SNI, verification on; report expired / hostname mismatch / untrusted chain / expires < 7 d as separate flags; "connection error" is not "untrusted" |
| 7.8 | SSRF guard | Resolve hostname; reject loopback, RFC1918, link-local (incl. 169.254.169.254), multicast, IPv6 equivalents; connect to the resolved IP; port 443 only for TLS; same guard for RDAP (fixed host `rdap.org` only) |
| 7.9 | Check transparency | Response adds `checks: {web_risk, rdap, tls}` each `ok|skipped|failed|unknown`; UI shows "limited check" when live checks failed |
| 7.10 | Interstitial endpoint | Remove static `/api/interstitial`, or make it evaluate the URL with the same engine and return the structured reasons for the extension page |
| 7.11 | Drainer patterns | Keep patterns; add negative samples (legit `uniswap.org`, `opensea.io`) and word-boundary matching |
| 7.12 | Test hygiene | Replace live RDAP/SSL in tests with mocks (respx / monkeypatch); one opt-in `live_smoke` marker |

## Proof tests
`test_top1000_domains_never_dangerous` (use a pinned snapshot of a public top-sites list stored under `tests/data/`) · `test_brand_official_domains_not_flagged` (`google.co.in`, `amazon.in`, `paypal.me`, `microsoft.com`, `sbi.co.in`) · `test_brand_lookalikes_flagged` (`paypa1-login.xyz`, `g00gle-secure.top`) · `test_ssrf_targets_blocked` (127.0.0.1, 10.x, 169.254.169.254, `localhost`, DNS names resolving to private IPs) · `test_non_http_schemes_rejected` · `test_unknown_rdap_never_blocks` · `test_score_table` · `test_subdomain_rdap_uses_registrable_domain` · `test_concurrent_scans_do_not_block` (50 parallel scans with mocked 2 s upstream finish in ≈ 2–3 s).

## Verification
Manually scan 30 benign sites (banks, universities, Indian gov/e-commerce sites, CDNs) and 30 known-bad samples from public test feeds (use Google's Safe Browsing test pages and well-known phishing test URLs only; never visit live phishing pages unprotected). Record false positives/negatives in a table; zero false "Dangerous" is the gate.

## Exit gate
Top-1000 test green · SSRF tests green · latency target met with mocks · scoring table documented.
