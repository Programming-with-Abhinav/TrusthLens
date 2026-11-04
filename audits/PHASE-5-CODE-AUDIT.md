# Phase 5 Code Audit Report (Task 5.0)

**Date:** 2026-11-04  
**Auditor:** Coding Agent  
**Scope:** `extension/`, `static/`, `my-vibe-app/`, `supabase/schema.sql`, `migrations/`, `.github/workflows/ci.yml`, `.dockerignore`.

---

## 1. Chrome MV3 Extension (`extension/`)
- **Manifest (`manifest.json`):**
  - Manifest V3 compliant.
  - Permissions: `activeTab`, `storage`, `clipboardWrite`.
  - Host permissions: `*://*/*` (needed for active link scanning and navigation check).
  - Background: service worker `background.js`.
- **Security & DOM (`content.js`):**
  - Shadow DOM: Created using `host.attachShadow({ mode: "closed" })` preventing host page tampering.
  - DOM APIs: Uses `createElement`, `textContent`, `setAttribute`, and `appendChild`. Strictly zero `innerHTML`, `outerHTML`, or `insertAdjacentHTML`.
  - Text extraction: Properly sanitizes and strips scripts, styles, forms, and ads.
- **Risks / Status:**
  - Background service worker communicates with the backend via fetch.
  - Interstitial redirect works as intended via `chrome.tabs.update`.

---

## 2. Static Prototype UI (`static/`)
- **Files:** `index.html`, `app.js`, `interactions.js`, `interstitial.html`, `style.css`.
- **Backend Mount:** `main.py` serves `static/` only in non-production environments (`ENV != "production"`).
- **Status:** Safe; isolated from production path.

---

## 3. Next.js 16 Web Application (`my-vibe-app/`)
- **Dependencies & Framework:** Next.js 16.4.3, React 19.3.0, `@supabase/ssr` 0.12.7, Tailwind CSS v4.
- **Service Role Key Hygiene:**
  - `SUPABASE_SERVICE_ROLE_KEY` is only imported in `lib/supabase/admin.ts` and `lib/supabase.ts`.
  - Used exclusively in Server Actions (`app/auth/actions.ts` for account deletion with `use server`).
  - Never referenced in client components (`"use client"`) or exported to `NEXT_PUBLIC_*`.
- **Auth & Routing:**
  - `middleware.ts` uses `createServerClient` and `supabase.auth.getUser()` to protect `/dashboard`.
  - In Next.js 16, migration to `proxy.ts` is planned for Phase 9.

---

## 4. Database & Migrations (`supabase/` & `migrations/`)
- **Supabase Schema (`supabase/schema.sql`, `supabase/migrations/001_trustlens_core.sql`):**
  - Tables: `profiles`, `usage_daily`.
  - RLS: Enabled on both tables (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`).
  - Policies: Users can SELECT their own profile and update only `display_name`. Users can only SELECT their own daily usage. No INSERT/UPDATE granted to `anon` or `authenticated` on `usage_daily` (updates done via atomic RPC / service role).
  - Privacy: Zero claim text, query text, or URLs stored.
- **SQLite Migrations (`migrations/`):**
  - `001_core_entities.sql`: Sets up cache table.
  - `002_remove_history.sql`: Drops `trustlens_history` and `history` tables.

---

## 5. CI / CD Workflow (`.github/workflows/ci.yml`)
- **Backend Job:** Tests FastAPI backend with Python 3.12 using `pytest test_main.py -v`.
- **Frontend Job:** Builds Next.js frontend with Node 20 (`npm ci` + `npm run build`).

---

## 6. Docker & Container Hygiene (`.dockerignore`, `Dockerfile`)
- `.dockerignore` excludes `.env*` (except `.env.example`), `.venv`, `*.db`, `.git`, `node_modules`, `tests`.
- Prevents secrets or local databases from leaking into container images.
