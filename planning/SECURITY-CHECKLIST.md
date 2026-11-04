# Security Checklist (run at Phase 5 exit, Phase 11, and before every release)

Mark each item with evidence (test name, command output, screenshot). Any failed Critical item blocks release.

## Authentication & authorization
- [ ] Forged/unsigned/expired/wrong-audience JWT → 401 in all modes (**Critical**)
- [ ] Supabase outage never results in trusting token payload (**Critical**)
- [ ] Extension tokens stored hashed; revocation takes effect immediately
- [ ] Row-Level Security tested: user A cannot read/write user B's `profiles`/usage rows
- [ ] Service-role key only in server env; absent from client bundles and extension (**Critical**)
- [ ] Protected pages use `supabase.auth.getUser()`; redirect targets validated; generic auth errors
- [ ] Account deletion removes profile, usage, extension tokens

## Data & privacy
- [ ] Marker-string test: submitted claim/URL/page text appear in no DB, cache, or log (**Critical**)
- [ ] No history endpoint exposing content
- [ ] `trustlens.db` and any dump purged from repo, images, backups
- [ ] Privacy policy matches actual third-party calls (Fact Check, Web Risk, RDAP, Gemini)
- [ ] Retention: cache TTLs set; logs ≤ 30 days; error tracker scrubs PII

## API
- [ ] CORS allowlist only; credentials disabled
- [ ] Rate limits for anonymous, authenticated, and per-token; 429 + `Retry-After`
- [ ] Input size limits enforced (422/413)
- [ ] SSRF guard blocks private/loopback/link-local/metadata targets, including DNS rebinding (resolve then connect to IP)
- [ ] Errors never include stack traces, keys, or upstream URLs
- [ ] Security headers present (HSTS, nosniff, referrer policy, frame-ancestors)
- [ ] OpenAPI/docs disabled or protected in production

## LLM & prompt injection
- [ ] Claims/evidence/page text treated as untrusted; delimiters + sanitization
- [ ] Output validated (length, no foreign URLs); fallback on invalid output
- [ ] Separate Gemini key; spend cap and alert
- [ ] Injection sample set passes (≥ 20 samples)

## Extension
- [ ] Manifest permissions justified one by one; no `<all_urls>` unless justified
- [ ] No `innerHTML`/`eval`/remote code; closed Shadow DOM
- [ ] No network call on selection before user action; protection-mode disclosure accurate
- [ ] Tokens in `chrome.storage.local`; never logged
- [ ] Message handlers validate sender and payload

## Web app
- [ ] CSP in place and tested; no inline script without nonce
- [ ] XSS: results render as text; links `rel="noopener noreferrer"`, only http/https
- [ ] Open-redirect test: `?next=//evil.com`, `?next=https://evil.com`, `?next=/\evil.com`
- [ ] CSRF: server actions/state-changing routes protected
- [ ] Cookies: `HttpOnly`, `Secure`, `SameSite` set by Supabase SSR config

## Supply chain & infrastructure
- [ ] Lockfiles committed; `pip-audit` and `npm audit` show no high/critical
- [ ] gitleaks clean across history; leaked keys rotated
- [ ] Docker: non-root, pinned base, no secrets in layers, Trivy clean (high/critical)
- [ ] Secrets in platform secret manager; separate staging/production keys
- [ ] Backups/restore tested for Postgres; Redis treated as disposable
- [ ] TLS A-grade on both domains; HSTS preload considered after stability
- [ ] OWASP ZAP baseline scan: no high alerts

## Sign-off
Reviewer 1: ______ Reviewer 2: ______ Date: ______
