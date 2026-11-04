# Requirements — v1.1 Production Readiness

Status values: `Open` · `In progress` · `Implemented` · `Verified` (evidence linked in `STATE.md`).
Only `Verified` counts as done. All items start `Open` unless noted.

## SEC — Security
| ID | Requirement | Acceptance criteria | Phase |
|---|---|---|---|
| SEC-01 | Auth fails closed | Forged/unsigned/expired JWT → 401 in every config mode, including Supabase outage (→ 503 for authenticated routes, never trust payload) | 5 |
| SEC-02 | All callers rate-limited | Authenticated and anonymous limited separately; 429 with `Retry-After` | 5/8 |
| SEC-03 | CORS allowlist | Only configured origins; no wildcard with credentials | 5 |
| SEC-04 | Secrets hygiene | No secret in repo/image; gitleaks clean; keys rotated; separate keys per service | 5 |
| SEC-05 | Input limits | Claim text ≤ 5,000 chars; URL ≤ 2,048; summary ≤ 100,000; bodies over limit → 413/422 | 5 |
| SEC-06 | SSRF protection | Outbound probes only to public IPs, port 443; metadata/private ranges blocked | 7 |
| SEC-07 | Security headers | CSP, HSTS, X-Content-Type-Options, Referrer-Policy, frame-ancestors on site and API | 8/9 |
| SEC-08 | Dependency hygiene | Pinned lockfiles; `pip-audit` and `npm audit` in CI with no high/critical | 8 |
| SEC-09 | Prompt-injection resistance | Injection test set passes; LLM output validated | 6 |
| SEC-10 | Extension safety | No `innerHTML`; closed Shadow DOM; permission list justified | 10 |

## PRIV — Privacy
| ID | Requirement | Acceptance criteria | Phase |
|---|---|---|---|
| PRIV-01 | No raw content stored | DB/cache/log inspection after a test run contains none of the submitted strings | 5 |
| PRIV-02 | No history endpoint | `/api/history` removed or returns only the caller's own non-content metadata | 5 |
| PRIV-03 | Existing data purged | `trustlens.db` deleted from repo, images and hosts; `.gitignore` enforced | 5 |
| PRIV-04 | Log redaction | Structured logs carry route, status, duration, anonymized user flag only | 5/8 |
| PRIV-05 | Account deletion | Deletes profile + usage; verified by test and in staging | 9 |
| PRIV-06 | Disclosure | Privacy policy lists every third party and purpose; linked from site, extension and Store listing | 10 |

## TRUTH — Claim verification
| ID | Requirement | Acceptance criteria | Phase |
|---|---|---|---|
| TRUTH-01 | Correct verdict mapping | Table-driven test over ≥ 60 real rating strings; "Not true", "Inaccurate", "Half true" never map to Verified; unknown → "Unrated" | 6 |
| TRUTH-02 | Evidence-gated verdicts | Verdict returned only with ≥ 1 source URL; otherwise "Unverified" | 6 |
| TRUTH-03 | No weak-match guesses | 50 unrelated/true claims against local seed return Unverified | 6 |
| TRUTH-04 | Honest naming | No "NLI"/"embedding" claims in UI, API or docs unless implemented | 6 |
| TRUTH-05 | Calibrated output | Labels per DECISIONS D5; confidence replaced by evidence count + agreement | 6 |
| TRUTH-06 | Cache correctness | TTL; key = SHA-256(normalized claim + source mode); no claim text in value | 6/8 |
| TRUTH-07 | Parallel, bounded latency | Claims verified concurrently under an overall 6 s deadline; partial results flagged | 6 |
| TRUTH-08 | Claim splitting | Keeps ≥ 3-word claims; max 5; unit tests incl. abbreviations | 6 |
| TRUTH-09 | Demo mode explicit | Demo/seed answers visibly badged; disabled in production | 6 |

## URL — URL safety
| ID | Requirement | Acceptance criteria | Phase |
|---|---|---|---|
| URL-01 | Scheme/validation | http/https only; IDNA normalization; userinfo flagged | 7 |
| URL-02 | Registrable-domain logic | Public Suffix List used for brand, TLD, RDAP decisions | 7 |
| URL-03 | Trusted-domain precision | Top-1000 domains (e.g. Tranco list snapshot) → 0 "Dangerous", ≤ 1% any flag | 7 |
| URL-04 | Scored verdict | Documented weights; block only on corroborated signals or Web Risk hit | 7 |
| URL-05 | Domain age | RDAP via registrable domain; unknown shown as unknown; cached with TTL | 7 |
| URL-06 | TLS check | Async, bounded; expired/untrusted/mismatch flagged | 7 |
| URL-07 | Check transparency | Response lists which checks ran/failed (`web_risk`, `rdap`, `tls`) | 7 |
| URL-08 | Crypto-drainer patterns | Unit-tested on positive/negative samples | 7 |

## API — Gateway & operations
| ID | Requirement | Acceptance criteria | Phase |
|---|---|---|---|
| API-01 | Versioned routes | Every public route under `/api/v1/*`; legacy `/api/*` kept as aliases with a deprecation header | 8 |
| API-02 | Redis rate limit & cache | Shared across workers; survives restart | 8 |
| API-03 | Atomic usage counting | Concurrent test: N requests → exactly N counted; summaries counted | 8 |
| API-04 | Non-blocking I/O | No blocking socket/SQLite in request path; 50-concurrent test within p95 targets | 7/8 |
| API-05 | Typed config | App refuses to boot in production without required settings | 8 |
| API-06 | Health | `/healthz` (liveness), `/readyz` (cached dependency status) | 8 |
| API-07 | Observability | Request ID, structured logs, error tracking (e.g. Sentry), basic metrics | 8 |
| API-08 | Error contract | Uniform JSON errors `{code, message, request_id}`; no stack traces | 8 |
| API-09 | Container | Multi-stage, non-root, pinned base, no secrets, healthcheck, one Python version | 8 |
| API-10 | API-only in prod | No `static/` or `extension/` mounts; OpenAPI docs gated or disabled | 8 |
| SUM-01 | Summarizer retained | Keep current safeguards; add per-user cap and counting; Gemini key separate | 6/8 |

## UX — Web app (details in `UI-UX-SPEC.md`)
| ID | Requirement | Acceptance criteria | Phase |
|---|---|---|---|
| UX-01 | Design system | Tokens (color, type, spacing, radius, motion) implemented once; no ad-hoc styles | 9 |
| UX-02 | All screens & states | Every screen has loading, empty, error, rate-limited, offline states | 9 |
| UX-03 | Verdict clarity | Verdict = label + icon + color + source list; never color alone | 9 |
| UX-04 | Accessibility | WCAG 2.1 AA; keyboard-complete; screen-reader tested; 0 critical axe findings | 9 |
| UX-05 | Responsive | Works 320–1920 px; touch targets ≥ 44 px | 9 |
| UX-06 | Performance | LCP ≤ 2.5 s, CLS ≤ 0.1, INP ≤ 200 ms on mid-range mobile profile | 9 |
| UX-07 | Auth flows | Sign-up, sign-in, reset password, email verification, sign-out, delete account; generic errors | 9 |
| UX-08 | Dashboard | Real usage + caps, extension tokens (create/revoke), privacy controls | 9 |
| UX-09 | Content | Privacy, Terms, About/How it works, Contact, 404/500 pages | 9/10 |
| UX-10 | Next.js 16 conformance | `proxy.ts` in place of `middleware.ts`; Node 20.9+; build has no deprecation warnings | 9 |

## EXT — Extension
| ID | Requirement | Acceptance criteria | Phase |
|---|---|---|---|
| EXT-01 | Least privilege | Every manifest permission justified in writing; unneeded ones removed | 10 |
| EXT-02 | Safe auth | Per DECISIONS D6; no pasted long-lived tokens | 10 |
| EXT-03 | Privacy-preserving protection | Per DECISIONS D4; local-first heuristics | 10 |
| EXT-04 | Interstitial | Shown only on corroborated danger; clear "Go back" primary action; proceed requires explicit confirm | 10 |
| EXT-05 | Selection pill & popup UX | Per UI-UX-SPEC §6; keyboard accessible; no layout shift on host pages | 10 |
| EXT-06 | Store readiness | Listing, screenshots, single-purpose statement, permission justifications, hosted privacy policy, test instructions | 10 |
| EXT-07 | Versioned releases | Reproducible build zip; changelog; update path | 10 |

## QA — Quality & release
| ID | Requirement | Acceptance criteria | Phase |
|---|---|---|---|
| QA-01 | Hermetic tests | No live network in default test run | 11 |
| QA-02 | Coverage | Backend ≥ 85% lines, ≥ 95% on auth, verdict mapping, privacy modules | 11 |
| QA-03 | E2E | Playwright: sign-up → token → verify → delete account; extension smoke test | 11 |
| QA-04 | Load | k6 profile meets latency targets at agreed RPS | 11 |
| QA-05 | CI gates | Lint, types, tests, build, audit, secret scan, image scan all required for merge | 11 |
| QA-06 | Staging parity | Release candidate passes full checklist on staging with real keys | 11 |
| QA-07 | Docs truthfulness | `scripts/check_docs.py` (or review) confirms docs match code claims | 11 |
