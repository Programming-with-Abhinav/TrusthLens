# Roadmap — Milestone v1.1 "Production Readiness"

Continues from v1.0 phases 1–4 (prototype). Phase numbers 5–11 are the only numbering to use.
Effort figures are rough planning estimates for one full-time developer; revise after Phase 5.

```
5 Baseline + Security/Privacy ──┬─► 6 Truth engine ──┐
   (P0, blocks everything)      ├─► 7 URL scanner ───┼─► 8 API hardening ─► 10 Extension + Store ─► 11 QA + Release
                                └─► 9 Web UI/UX ─────┘        (9 design work may start during 5)
```

| Phase | Name | Depends on | Est. | Exit gate (all must be true) |
|---|---|---|---|---|
| 5 | Baseline, security & privacy | — | 4–6 d | No raw content stored/logged; forged JWT rejected; CORS locked; secrets clean; unseen code audited; docs replaced |
| 6 | Truth engine correctness | 5 | 5–7 d | Verdict-mapping and weak-match golden sets pass; honest naming; cache TTL; parallel verify |
| 7 | URL scanner accuracy | 5 | 5–7 d | Top-1000 domains: 0 Dangerous; SSRF blocked; async checks; scored verdicts |
| 8 | API production hardening | 5, 6, 7 | 6–8 d | Redis rate limit/cache; atomic usage; typed config; hardened container; observability; `/api/v1` parity |
| 9 | Web app UI/UX | 5 (design), 8 (integration) | 10–15 d | All screens/states per spec; WCAG 2.1 AA; Lighthouse budgets met; `proxy.ts` migrated |
| 10 | Extension & Store | 7, 8, 9 | 6–9 d | Manifest audited; safe auth; local-first protection; Store package complete |
| 11 | QA & release | all | 6–8 d | CI gates green; E2E + load pass on staging; release checklist 100% signed |

**Total ≈ 6–9 calendar weeks** for one developer (parallelizable with two).

## Phase gates
A phase is closed only when:
1. Every task is merged via reviewed PR.
2. Each defect/requirement it covers has evidence in `STATE.md`.
3. The phase's "Verification" section was executed by someone other than the author.
4. `RELEASE-CHECKLIST.md` items assigned to that phase are ticked.

## Deferred to v1.2
Stripe billing and plans, real semantic retrieval over a licensed/ingested ClaimReview corpus with embeddings and NLI, Firefox build, team features.
