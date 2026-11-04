# AGENTS.md — TrustLens AI (instructions for coding agents)

You are working on TrustLens AI: FastAPI API + Next.js 16 website (Supabase auth) + Chrome MV3 extension. The project is a **demo being converted to production**. Your job is to fix known defects safely, one small task at a time.

## 1. Source of truth (read before any task)

1. `planning/CLEANUP-AND-FIX-ROADMAP.md` — order of work and defect IDs (TL-xxx)
2. `planning/00-PROJECT-ANALYSIS.md` and `planning/AUDIT-2-CODEBASE-STATUS.md` — what is wrong and current status
3. `planning/phases/NN-*.md` — tasks, proof tests, exit gates for the current phase
4. `planning/DECISIONS.md` — owner decisions. **If a task depends on an unanswered decision, stop and ask.**
5. `planning/UI-UX-SPEC.md` — for any UI work
   If code and docs disagree, trust the code, report the mismatch, and fix the doc in the same change.

## 2. Work protocol (every task)

1. Restate the task and the defect IDs in one sentence. List the files you expect to touch.
2. Create a branch `fix/TL-xxx-short-name`.
3. **Write the failing test first** (proof test named in the phase file). Run it and confirm it fails for the right reason.
4. Make the smallest change that fixes it. No drive-by refactors.
5. Run the checks in section 5. Paste the real output tail in your report.
6. Append an evidence row to `planning/STATE.md` (date, TL id, test name).
7. Commit with message `fix(TL-xxx): summary`. Stop. Do not start the next task unprompted.

## 3. Hard rules (never break)

**Privacy**

- Never store or log raw claim text, URLs, or page text — not in SQLite/Redis values, logs, errors, exceptions, Sentry, or test snapshots. Cache keys are SHA-256 of normalized text; values contain no input text.
- Do not add analytics or telemetry that includes user content.

**Security**

- Auth fails closed. Never trust an unverified JWT payload. Never add a code path that treats a malformed/unknown token as a valid user.
- No secrets in code, tests, examples, logs, or commits. `.env*` stays untracked (except `*.example` with placeholders).
- CORS: explicit allowlist, no wildcard with credentials.
- Extension: no `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`eval`; closed Shadow DOM; do not add or widen permissions or host matches without a written justification and human approval.
- Outbound requests to user-supplied hosts must pass the SSRF guard.

**Correctness (truth engine)**

- A claim result with no source URL is **always** `Unverified`. Never invent or guess a verdict.
- Rating → verdict mapping is table-driven and negation-aware; unknown rating → `Unrated` (never `Mixed`, never `Verified`).
- Do not name or describe anything as "NLI", "cross-encoder" or "embeddings" unless it truly is.
- URL scanner: block only on corroborated signals or a Web Risk hit; unknown/failed live checks never block; official brand domains must not be flagged.

**Process**

- **Never weaken, delete, skip, or loosen a test to make it pass.** If a test seems wrong, stop and explain.
- No live network calls in tests; mock Google, RDAP, SSL, Supabase, Gemini.
- Do not delete files except those on the approved list in `planning/CLEANUP-AND-FIX-ROADMAP.md` Part A, and only via the protocol there (grep references first).
- Do not hand-edit lockfiles or generated files. Do not add dependencies without stating name, version, license, and reason.
- Do not change a public API response shape without updating tests, `/api/v1` and legacy routes together, and docs.
- Never claim "done", "fixed", "verified" or "all tests pass" without command output proving it. If you could not run something, say so.
- If unsure about a fact (library behavior, policy, version), write `VERIFY:` and say what to check. Do not guess.

## 4. Stop and ask a human when

- A decision D1–D15 is needed, or requirements conflict.
- The change touches auth, CORS, logging, storage, migrations, RLS, or the extension manifest (needs human review).
- A test still fails after two honest attempts.
- You would need to delete or rewrite more than ~200 lines outside the task's scope.
- You find a new bug: record it as a new TL-xxx row in `planning/AUDIT-2-CODEBASE-STATUS.md` instead of silently fixing it.

## 5. Commands (Windows PowerShell; adapt for macOS/Linux)

```powershell
.venv\Scripts\python.exe -m pytest -q                       # backend tests
.venv\Scripts\python.exe -m ruff check .                    # lint (after Phase 8 setup)
.venv\Scripts\python.exe scripts\guardrails.py              # project guardrail scan
.venv\Scripts\python.exe -m uvicorn main:app --reload --port 5500
cd my-vibe-app; npm ci; npm run build; npm run lint
.\scripts\verify.ps1                                        # runs all of the above
```

Versions: Python 3.12 · Node 20.9+ · Next.js 16 (`proxy.ts`, not `middleware.ts`).

## 6. Code conventions

- Python: type hints, async I/O only in request paths (no blocking sockets/SQLite), `asyncio.gather` for independent upstream calls with timeouts, typed settings (pydantic-settings), small pure functions for logic (easy to test).
- Routes: one router mounted at `/api/v1` and legacy `/api` (legacy adds `Deprecation` header).
- Errors: `{code, message, request_id}`; never leak stack traces, keys, or upstream URLs.
- TypeScript: strict; server-only code in server modules; no `SUPABASE_SERVICE_ROLE_KEY` in client bundles; API base URL from `NEXT_PUBLIC_API_BASE_URL` only.
- UI: follow `planning/UI-UX-SPEC.md` tokens and states; verdicts always label + icon + color.

## 7. Report format (end of every task)

```
Task: <TL ids> <one line>
Files changed: <list>
Tests added/updated: <names>
Commands run + result: <pasted tails>
Evidence row added to STATE.md: yes/no
Not done / risks / VERIFY items: <list>
Next suggested task: <one line>
```
