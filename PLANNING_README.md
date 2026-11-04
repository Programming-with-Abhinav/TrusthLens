# TrustLens AI — Production Planning Folder (Milestone v1.1)

**Purpose:** convert the working demo into a production-ready, privacy-safe website, API and Chrome extension, with a redesigned UI/UX and a release process that catches mistakes before users do.
**Written:** 2026-10-24 · **Replaces:** the v1.0 `.planning/` files, which overstate completion (see `00-PROJECT-ANALYSIS.md`).

## Read in this order

| # | File | Read it to… |
|---|---|---|
| 1 | `00-PROJECT-ANALYSIS.md` | Understand what exists, what is wrong, and the defect register (TL-xxx IDs) |
| 2 | `DECISIONS.md` | Resolve the 10 owner decisions that block work. **Do this first.** |
| 3 | `PROJECT.md` | Know what the product is and is not (corrected) |
| 4 | `REQUIREMENTS.md` | See every production requirement with acceptance criteria |
| 5 | `ROADMAP.md` | See phase order, dependencies and exit gates |
| 6 | `phases/05…11-*.md` | Execute. One file per phase with tasks, tests and evidence needed |
| 7 | `UI-UX-SPEC.md` | Build the redesigned web app, extension UI and interstitial |
| 8 | `SECURITY-CHECKLIST.md`, `TEST-PLAN.md` | Verify |
| 9 | `DEPLOYMENT-RUNBOOK.md`, `RELEASE-CHECKLIST.md` | Ship and roll back |
| 10 | `STATE.md` | Keep the honest current status |

## Ground rules (these are what prevent mistakes)

1. **Nothing is "complete" without evidence.** A requirement or defect is closed only when `STATE.md` links the passing test name, a CI run, or a dated screenshot. "Implemented" is not "verified".
2. **Fix order is fixed:** privacy/security (Phase 5) before anything user-facing. Do not ship UI polish on top of a leaking backend.
3. **Docs follow code, never the reverse.** If a document claims a capability the code lacks (e.g. "cross-encoder NLI"), change the document or build the capability in the same pull request.
4. **No live network in unit tests.** External calls (Google, RDAP, SSL, Supabase, Gemini) are mocked; a small separate "live smoke" suite runs only on demand.
5. **Two-person rule** for security-sensitive changes (auth, logging, CORS, storage, extension permissions).
6. **One source of truth for numbering:** phases 5–11 in this milestone; requirement IDs in `REQUIREMENTS.md`; defect IDs `TL-xxx`.
7. **Unseen code must be audited before it is trusted.** The extension, static UI, Next.js app, SQL migrations and CI workflow were not available when this plan was written (see "Not audited" in the analysis). Phase 5 task 5.0 closes that gap.

## Folder map

```
planning/
├── README.md
├── 00-PROJECT-ANALYSIS.md     architecture, gaps, defect register
├── DECISIONS.md               10 owner decisions with recommendations
├── PROJECT.md                 corrected project definition
├── REQUIREMENTS.md           production requirements + acceptance criteria
├── ROADMAP.md                 phases 5–11, dependencies, exit gates
├── STATE.md                   honest current status (update every PR)
├── UI-UX-SPEC.md              design direction, screens, states, a11y, copy
├── SECURITY-CHECKLIST.md
├── TEST-PLAN.md
├── DEPLOYMENT-RUNBOOK.md
├── RELEASE-CHECKLIST.md       go/no-go gate
└── phases/
    ├── 05-baseline-security-privacy.md
    ├── 06-truth-engine-correctness.md
    ├── 07-url-scanner-accuracy.md
    ├── 08-api-production-hardening.md
    ├── 09-web-app-ui-ux.md
    ├── 10-extension-and-store.md
    └── 11-qa-and-release.md
```

## Limits of this plan (read once)

No plan can guarantee zero mistakes. This one reduces the odds by making every claim testable, ordering work by risk, and adding release gates. Items marked **VERIFY** are things the author could not confirm from the files provided.
