# Phase 10 — Chrome Extension & Web Store

**Goal:** a least-privilege, privacy-respecting extension that passes Chrome Web Store review.
**Covers:** TL-012, 045, 082 · EXT-01–07 · SEC-10 · PRIV-06.
**Depends on:** Phases 7, 8, 9 · DECISIONS D4, D6, D9.

## Tasks
| ID | Task | Detail |
|---|---|---|
| 10.0 | Manifest audit | List every permission, host permission, content-script match, and web-accessible resource. For each: feature that needs it, narrower alternative, decision. Remove anything unjustified. If interception needs more than `activeTab`/`storage`, update the docs (FR-E5) and the Store justification honestly. Check current Chrome MV3 policy docs at submission time — policies change |
| 10.1 | Code safety scan | `grep -R "innerHTML\|outerHTML\|insertAdjacentHTML\|eval(\|new Function"` → zero in `extension/`; closed Shadow DOM verified in tests; Content-Security-Policy in manifest has no remote code |
| 10.2 | Auth (D6) | Dashboard creates a named, revocable extension token (random, hashed at rest, shown once). Options page accepts it; stored in `chrome.storage.local` (not sync). Backend validates by hash lookup, per-token rate limit. Remove "paste Supabase session token" flow |
| 10.3 | Local-first protection (D4) | Navigation checks run local heuristics first (same rules as Phase 7, bundled). Only call the API when the local score crosses a threshold or the user presses "Check this page". Optional "Protection mode" toggle explains exactly what is sent |
| 10.4 | Interstitial | Shows only on corroborated danger (Web Risk hit or high score with multiple signal families). Primary action "Go back to safety"; secondary "Proceed anyway" behind a confirm step; reasons listed in plain language; accessible (focus, ARIA, keyboard) |
| 10.5 | Selection pill | Appears on text selection ≥ 4 words with a keyboard shortcut alternative; closed Shadow DOM; does not shift host layout; dismiss with Esc; respects `prefers-reduced-motion`; no data sent until the user clicks Check |
| 10.6 | Popup | Page scan result with reasons, "Check selected text", "Summarize page" (user-triggered), link to dashboard; loading/error/offline states; works signed out with anonymous limits |
| 10.7 | Options | Backend URL fixed to production by default (custom URL only in an "Advanced" section, HTTPS enforced); token management; privacy summary |
| 10.8 | Build & release | Reproducible build script producing `trustlens-<version>.zip`; version bump + changelog; source map policy; CI artifact |
| 10.9 | Store package | Name, short and detailed description, category, 128 px icon, screenshots (use the size the Store currently requires), promo tile, single-purpose statement, permission justifications, data-usage disclosures matching the privacy policy, hosted privacy policy URL, support email, test instructions and a test account for reviewers |
| 10.10 | Compatibility | Test on current stable Chrome and Edge (Chromium), Windows + macOS; Chrome profiles with enterprise policies not required |
| 10.11 | Staged rollout | Publish unlisted → trusted testers → public; monitor errors and reviews |

## Proof tests
Playwright with the extension loaded (persistent context): pill appears and is keyboard operable · interstitial blocks a Safe Browsing test URL and "Go back" works · benign sites never show interstitial (50-site list) · no network request on selection until Check clicked (assert via request interception) · token revoke → next call 401 and UI shows re-auth · manifest snapshot test fails CI if permissions change without review.

## Verification
Fresh Chrome profile, install the zip, complete the reviewer test script in the Store package; second person repeats it on Windows and macOS.

## Exit gate
Manifest audit signed · Store package complete · unlisted listing passes review · D9 legal review done.
