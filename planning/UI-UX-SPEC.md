# UI/UX Specification — TrustLens AI

**Status:** proposal pending owner approval (DECISIONS D10). The existing UI was not available when this was written, so Phase 9 task 9.0 audits it first and this spec is adjusted for anything already good.
**Applies to:** website, dashboard, extension (pill, popup, options, interstitial).

## 1. Experience principles
1. **Answer first, evidence second.** The verdict and the reason come before any detail; sources are one glance away.
2. **Say what we don't know.** "Unverified" is a normal, respected outcome, not an error.
3. **Never color alone.** Every state has label + icon + color.
4. **Calm under risk.** Warnings are clear and firm, never alarmist or shaming.
5. **Privacy visible.** Show when anything leaves the device, and why.
6. **Usable in two taps.** Check a claim or a link from the first screen, signed out.

## 2. Visual direction (proposal)
**Concept: "the evidence desk."** A reference-library feel: calm paper-like surfaces, strong editorial type, and index-card style result cards that read like a fact-checker's file. It signals care and credibility and avoids generic security-product clichés (neon shields, dark gradients, big green "100%" numbers).

**Tokens** (verify every pairing with a contrast checker; targets: text ≥ 4.5:1, large text/UI ≥ 3:1)
| Token | Light | Dark | Use |
|---|---|---|---|
| `--paper` | `#F7F4EE` | `#14161A` | page background |
| `--card` | `#FFFFFF` | `#1C1F25` | cards |
| `--ink` | `#16181D` | `#ECEAE4` | body text |
| `--ink-muted` | `#4A5160` | `#A9AFBC` | secondary text |
| `--rule` | `#D9D4C8` | `#2E323B` | borders |
| `--accent` | `#1F4E5F` | `#7CC0D4` | links, primary buttons |
| `--v-true` | `#1B6B3A` | `#6FD09A` | True / Mostly true |
| `--v-mixed` | `#7A5A00` | `#E3BE5A` | Mixed |
| `--v-misleading` | `#A24A00` | `#F0A263` | Misleading |
| `--v-false` | `#A8261E` | `#FF8F86` | False / Dangerous |
| `--v-unverified` | `#4A5160` | `#A9AFBC` | Unverified / Unknown |

Typography: display **Fraunces** (or another characterful serif), UI **IBM Plex Sans**, URLs/code **IBM Plex Mono**; self-hosted, `font-display: swap`, 2 families max plus mono. Scale 14 / 16 / 18 / 22 / 28 / 40 / 56; body 16–18 px, line-height 1.5–1.6, max line length 70 ch.
Spacing: 4-pt grid (4, 8, 12, 16, 24, 32, 48, 64). Radius: 6 (inputs), 10 (cards). Motion: 120–200 ms ease-out; none if `prefers-reduced-motion`.
Dark mode: follow system, user toggle in footer/account.

## 3. Information architecture
```
/                    Landing + live checker (signed out OK)
/how-it-works        Sources, method, limits
/check               Workbench (Claims · Links · Summarize)
/login /signup /reset /verify
/dashboard           Usage · Extension tokens · Privacy · Account
/extension           Install + connect guide
/privacy /terms /contact
404 · 500 · offline
```
Header: logo, Check, How it works, Extension, Sign in (or avatar menu). Footer: Privacy, Terms, Contact, theme toggle, "Not a guarantee of truth or safety."

## 4. Screens

### 4.1 Landing (`/`)
- **Hero = the product.** Headline in plain words ("Check a claim or a link before you share it."), one large input ("Paste a claim or a link"), a primary "Check" button, three example chips. Works signed out; shows remaining free checks.
- Below: "How we decide" (3 steps: find fact-checks → show who said what → say 'unverified' when nothing exists), the privacy promise (what we store: nothing you check), extension call to action, FAQ.
- No stats row, no stock illustrations, no unverifiable "99% accurate" claims.

### 4.2 Workbench (`/check`)
- Input auto-detects claim vs link; tabs (Claims / Links / Summarize) are visible so users can override.
- **Claim result card** (one per extracted claim, max 5): verdict badge (label + icon), one-sentence plain-language summary, "What fact-checkers say" list (publisher, their rating, date, external link), "Checked just now / from cache (age)", feedback "Report a problem". No numeric score.
- **Link result card:** level badge (Safe-looking / Caution / Suspicious / Dangerous — see §5), top 3 reasons in plain words, expandable "All checks" (Web Risk, domain age, certificate) with ok/unknown/failed states, "Open anyway" is never a primary button.
- **Summarize:** paste text or Wikipedia link; length toggle; result = summary + key points; note "Summary generated from the text you supplied."
- **States:** idle · validating · loading (skeleton + "Checking sources…" with live region) · partial results · success · no evidence · error (with retry) · rate-limited (countdown + sign-in prompt) · offline.

### 4.3 Auth screens
Single-column card; labels above inputs; password rules visible before typing; show/hide password; Google button + divider; inline field errors tied via `aria-describedby`; generic failure copy ("That email or password didn't work."); verification and reset screens have clear next steps and resend with cooldown.

### 4.4 Dashboard
- **Today:** usage meters (claims, links, summaries) with real caps or "no cap" text.
- **Extension:** step-by-step connect, token list (name, created, last used, Revoke), "Create token" flow shows the token once with a copy button.
- **Privacy:** plain list of what is stored (email, display name, daily counts) and what is not; Download my data (optional); **Delete account** requires typing the email.
- Empty state for new users with a "Run your first check" button.

### 4.5 Content pages
How it works (sources, ratings explained, limits), Privacy, Terms, Contact. Reading level ≤ grade 8, headings navigable, last-updated date.

## 5. Verdict & risk language

**Claims**
| Label | Icon | Meaning (shown on hover/expand) |
|---|---|---|
| True | check-circle | Fact-checkers rate this accurate |
| Mostly true | check-half | Accurate with minor caveats |
| Mixed | scale | Fact-checkers disagree or rate it partly true |
| Misleading | alert-triangle | Contains true elements but gives a false impression |
| False | x-circle | Fact-checkers rate this false |
| Unverified | help-circle | We found no fact-check for this claim. That does not mean it is true or false |

**Links**
| Label | Meaning |
|---|---|
| No warning signs found | No signals fired. Not a guarantee of safety |
| Caution | A weak signal (e.g. no HTTPS). Be careful with personal info |
| Suspicious | Several signals match scam patterns |
| Dangerous | Reported by Google Web Risk or strongly matches phishing/drainer patterns. Don't enter any information |
Never use the word "Safe" alone.

## 6. Extension UI
- **Selection pill:** small, appears near the selection after a short delay; label "Check claim"; Enter/Space activates; Esc dismisses; keyboard shortcut (e.g. Alt+Shift+C) as alternative; result opens as a compact card anchored to the selection (closed Shadow DOM, safe DOM APIs only).
- **Popup (360 px wide):** current site + level badge + top reasons; buttons "Check selected text", "Summarize page"; footer link to dashboard; signed-out banner with limits.
- **Options:** sign-in/token, protection mode toggle with "what is sent" explainer, advanced backend URL (HTTPS only).
- **Interstitial (full page):** red-toned but calm; headline "This site may be dangerous"; reasons list (plain words); primary "Go back to safety"; secondary text-button "I understand the risk — continue" requiring a confirm click; "Why am I seeing this?" and "Report a mistake" links; keyboard focus starts on the primary action.

## 7. Microcopy
| Situation | Copy |
|---|---|
| Input placeholder | "Paste a claim or a link" |
| Loading | "Checking fact-check sources…" / "Looking at this link…" |
| No evidence | "We couldn't find a fact-check for this claim. That doesn't make it true or false." |
| Rate limited | "You've reached the free limit for now. Try again in {n} min, or sign in for a higher limit." |
| Upstream down | "A source we rely on isn't responding. Showing what we could check." |
| Network error | "You appear to be offline. Check your connection and try again." |
| Auth failure | "That email or password didn't work." |
| Weak password | "Use at least 8 characters." |
| Token created | "Copy this now. For your security we won't show it again." |
| Delete account | "This permanently deletes your account and usage counts. Type your email to confirm." |
| Disclaimer | "TrustLens reports what fact-checkers and security feeds say. It isn't a guarantee of truth or safety." |
Voice: plain, direct, no fear-mongering, no jargon (avoid "NLI", "heuristics", "telemetry").

## 8. Accessibility (WCAG 2.1 AA minimum)
Semantic landmarks and heading order · all controls reachable and operable by keyboard · visible focus ring (≥ 3:1) · touch targets ≥ 44 px · form labels and error association · results announced via `aria-live="polite"` · verdicts never color-only · contrast verified for both themes · zoom to 200% and 400% reflow without loss · `prefers-reduced-motion` respected · no keyboard traps in dialogs (focus trap + restore) · captions/alt for any media · tested with NVDA (Windows) and VoiceOver (macOS/iOS).

## 9. Responsive rules
Breakpoints 360, 640, 768, 1024, 1280. Mobile: single column, sticky "Check" button, bottom-sheet results. Desktop: input left/results right at ≥ 1024. No horizontal scroll at 320 px.

## 10. Performance budgets
Landing JS ≤ 170 KB gzip · LCP ≤ 2.5 s · CLS ≤ 0.1 · INP ≤ 200 ms (mid-range mobile profile) · fonts self-hosted and subset · no layout shift when results appear (reserve space with skeletons).

## 11. Definition of done for any screen
All states built · keyboard-only pass · axe 0 critical/serious · contrast checked in both themes · copy from the table or reviewed · responsive at 320/768/1280 · screenshot attached to `STATE.md` evidence log.
