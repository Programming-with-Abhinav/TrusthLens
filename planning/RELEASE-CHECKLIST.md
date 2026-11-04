# Release Checklist — go/no-go

Two people sign. "Evidence" = link to test run, command output, or screenshot. Any unchecked **Critical** item is a no-go.

## A. Code & CI
- [ ] All CI gates green on the release candidate commit (**Critical**)
- [ ] No open Critical/High defects in the register (**Critical**)
- [ ] Coverage thresholds met (QA-02)
- [ ] Dependency and image scans clean of high/critical

## B. Privacy & security (**Critical block**)
- [ ] Marker-string privacy test passes on staging
- [ ] Forged-token tests pass on staging (configured mode)
- [ ] SECURITY-CHECKLIST signed
- [ ] Privacy policy and Store disclosures match real data flows
- [ ] Old `trustlens.db` and exposed keys purged/rotated

## C. Correctness
- [ ] Rating-table and claims golden sets pass; manual review of 20 outputs with real keys: 0 inversions
- [ ] Top-1000 domains: 0 Dangerous
- [ ] Safe Browsing test URLs flagged Dangerous
- [ ] Demo/seed mode off in production; no "NLI/embedding" wording anywhere

## D. Performance & reliability
- [ ] Load test targets met (p95 verify ≤ 2 s warm, scan ≤ 1.5 s)
- [ ] Chaos drills: Redis, Supabase, Google, Gemini failures degrade clearly
- [ ] Health, readiness, alerts, and on-call verified with a test alert
- [ ] Rollback rehearsed within the last 7 days

## E. UI/UX
- [ ] Every screen and state per `UI-UX-SPEC.md` built (screenshots linked)
- [ ] axe: 0 critical/serious on all routes; keyboard-only and screen-reader passes done
- [ ] Lighthouse budgets met (landing and workbench)
- [ ] Usability gate met (≥ 4/5 complete each core task)
- [ ] Copy reviewed; disclaimers present; 404/500/offline pages work

## F. Extension
- [ ] Manifest audit signed; permissions match docs and Store justifications
- [ ] No pre-click network on selection; interstitial gating verified; token revocation verified
- [ ] Fresh-profile install test on Windows and macOS
- [ ] Store package complete; unlisted listing approved

## G. Operations & docs
- [ ] Production env vars verified by the boot check; separate keys from staging
- [ ] Budgets/alerts set for Google, Gemini, hosting
- [ ] `STATE.md`, README, runbook match reality (docs check passed)
- [ ] Support email monitored; status page or announcement channel ready

## Decision
GO / NO-GO: ______ · Release owner: ______ · Reviewer: ______ · Date/time: ______ · Image digest: ______
