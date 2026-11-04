# TrustLens AI – Product Requirements Document (PRD)

**Document Version:** 2.2 (Milestone 1 Complete Baseline & Milestone 2 Enterprise Roadmap)  
**Date:** Current Baseline (October 2026)  
**Target Codebase:** FastAPI Microservice Gateway, Semantic Truth Engine, Deep Safety Engine, Next.js 16 Web Dashboard, Supabase Auth/PostgreSQL, Chrome MV3 Extension (Service Worker & Interstitial), GSD Core v1.16.0, CodeRabbit, GitHub Actions CI/CD  

---

## 1. Executive Summary

TrustLens AI is a unified, privacy-first web verification and safety platform that bridges the gap between factual misinformation and cyber fraud (phishing, brand impersonation, and Web3 crypto-drainers). It delivers real-time, in-context protection directly within the browser without requiring users to leave the page or sacrifice personal browsing privacy.

The platform architecture is divided into two major milestones:
1. **Milestone 1.0 (Production Baseline - 100% Completed)**: Comprises 4 architectural phases fully implemented and verified in the codebase:
   - **Truth Engine (Claims)**: Atomic claim extraction (capped at 5 claims), Google Fact Check Tools API client, local demo keyword fallback, embedded **Semantic Hybrid Retrieval (BM25 + Dense Vector Cosine Similarity with Reciprocal Rank Fusion)**, **NLI Stance Classification** (`Supports`, `Refutes`, `Neutral`), publisher authority weighting, temporal decay scoring, and **grounded evidence synthesis** with prompt-injection defense.
   - **Safety Engine (URLs)**: 9 local heuristic risk vectors, Google Web Risk client, **live RDAP domain registration age lookups** (flagging zero-day domains <30 days old), **live SSL/TLS socket telemetry**, **Web3 crypto-drainer inspection** (`permit2`, `seaport`, `setApprovalForAll`, `airdrop-claim`), and **pre-navigation warning interstitials** (`interstitial.html`).
   - **User Accounts & Dashboard**: Next.js 16 (React 19) web application with **Supabase SSR authentication** (Email/password and Google OAuth), server-validated route gating (`getUser()`), open-redirect defense, daily aggregate usage metrics tracking, extension session token provisioning, and self-service account deletion.
   - **Chrome MV3 Extension**: Browser overlay isolated inside a **closed Shadow DOM** (`attachShadow({ mode: "closed" })`) using safe DOM APIs (strictly zero `innerHTML`), popup active tab security inspector, configurable options storage sync, and background navigation service worker.
   - **DevOps & Quality Engineering**: 15-test pytest suite (100% pass rate), Next.js Turbopack build (zero errors), Docker containerization, Chrome Web Store assets, CodeRabbit AI review, Roo Code Nightly workspace rules, and GitHub Actions CI/CD pipeline.

2. **Milestone 2.0 (Enterprise Scaling & Next Roadmap - Remaining to Complete)**: Comprises Phases 5 & 6 designed for high-concurrency cloud scaling, enterprise monetisation, multi-modal vision intelligence, and automated browser store deployments.

---

## 2. Complete Execution Status Matrix

This matrix provides full transparency into **what has been completed** (Milestone 1.0) and **what remains to be completed** (Milestone 2.0).

### 2.1 Completed Requirements (Milestone 1.0 Baseline — 100% Verified)

```
┌────────────────────────────────────────────────────────┬─────────────┬─────────────────────────────────────────────────────────┐
│ Functional Requirement / Subsystem                     │ Status      │ Implementation File                                     │
├────────────────────────────────────────────────────────┼─────────────┼─────────────────────────────────────────────────────────┤
│ FR-C1: Dual Claim Verification Routes                  │ COMPLETED   │ main.py:227 (/api/verify & /api/v1/verify/claim)        │
│ FR-C2: Atomic Claim Splitting (Max 5 Claims)           │ COMPLETED   │ main.py:64 (split_claims)                                │
│ FR-C3: Google Fact Check Tools API Client              │ COMPLETED   │ main.py:161                                             │
│ FR-C4: Normalized Verdicts & Source Attribution        │ COMPLETED   │ main.py:151                                             │
│ FR-C5: Explicit "No evidence found" Missing Handling   │ COMPLETED   │ main.py:153                                             │
│ FR-C7: Semantic Hybrid Retrieval (BM25 + Dense Vectors)│ COMPLETED   │ claims_engine.py:143 (SemanticTruthEngine, RRF)         │
│ FR-C8: NLI Stance Classification & Composite Trust     │ COMPLETED   │ claims_engine.py:187, 218 (classify_nli_stance)         │
│ FR-C9: Grounded Evidence Synthesis (Gemini RAG)        │ COMPLETED   │ claims_engine.py:252 (synthesize_grounded_explanation)  │
│                                                        │             │                                                         │
│ FR-U1: Dual URL Security Scanner Routes                │ COMPLETED   │ main.py:263 (/api/scan & /api/v1/scan/url)              │
│ FR-U2: Multi-Vector Heuristic Analyzer (9 vectors)     │ COMPLETED   │ main.py:114 (analyze_url_heuristics)                    │
│ FR-U3: Google Web Risk API Optional Client             │ COMPLETED   │ main.py:286                                             │
│ FR-U4: URL Normalizer & Validator (HTTP 400 guard)     │ COMPLETED   │ main.py:99 (validate_and_normalize_url)                 │
│ FR-U5: Plain-Language Human Flag Explanations          │ COMPLETED   │ main.py:84 (FLAG_EXPLANATIONS)                          │
│ FR-U6: RDAP Domain Age & Live SSL Socket Telemetry     │ COMPLETED   │ url_scanner.py:35, 60 (lookup_domain_age, check_ssl)    │
│ FR-U7: Web3 & Crypto-Drainer Pattern Detection         │ COMPLETED   │ url_scanner.py:100 (analyze_crypto_drainers)            │
│ FR-U8: Pre-Navigation Warning Interstitial Screen      │ COMPLETED   │ extension/interstitial.html, static/interstitial.html   │
│                                                        │             │                                                         │
│ FR-A1: Email/Password Registration (min 8 chars)       │ COMPLETED   │ my-vibe-app/app/signup/page.tsx:28                      │
│ FR-A2: Email/Password & Google OAuth Authentication    │ COMPLETED   │ my-vibe-app/app/login/page.tsx:39                       │
│ FR-A3: Auth Code Exchange Callback                     │ COMPLETED   │ my-vibe-app/app/auth/callback/route.ts:1                │
│ FR-A4: Server Route Gating via getUser()               │ COMPLETED   │ my-vibe-app/middleware.ts:1                             │
│ FR-A5: Same-Site Relative Open-Redirect Defense        │ COMPLETED   │ my-vibe-app/lib/auth-utils.ts:1                         │
│ FR-A6: Privacy-Preserving Generic Auth Error Messages  │ COMPLETED   │ my-vibe-app/app/auth/actions.ts:18                      │
│ FR-A7: Authenticated User Metrics Dashboard            │ COMPLETED   │ my-vibe-app/app/dashboard/page.tsx:19                   │
│ FR-A8: Secure Session Sign Out                         │ COMPLETED   │ my-vibe-app/app/auth/actions.ts:46                      │
│ FR-A9: FastAPI Bearer JWT Token Verification           │ COMPLETED   │ supabase_client.py:47 (verify_token)                    │
│ FR-A10: Aggregate Daily Usage Counting (No Claims/URLs)│ COMPLETED   │ supabase_client.py:96 (record_claim_check)              │
│ FR-A11: Self-Service Account Deletion Flow             │ COMPLETED   │ my-vibe-app/app/auth/actions.ts:52                      │
│                                                        │             │                                                         │
│ FR-E1: In-Page Text Selection Fact-Check Overlay       │ COMPLETED   │ extension/content.js:47                                 │
│ FR-E2: Active Tab Security Scanner Popup               │ COMPLETED   │ extension/popup.js:14                                   │
│ FR-E3: Configurable Backend Service URL                │ COMPLETED   │ extension/options.js:9                                  │
│ FR-E4: Safe DOM APIs Only (Strictly zero innerHTML)    │ COMPLETED   │ extension/content.js:17, popup.js:53                    │
│ FR-E5: Principle of Least Privilege Permissions        │ COMPLETED   │ extension/manifest.json:6 (activeTab, storage)          │
│ FR-E6: Closed Shadow DOM CSS Tamper Defense            │ COMPLETED   │ extension/content.js:5 (attachShadow closed)            │
│ FR-E7: In-Page Claim Detection Badges in Extension     │ COMPLETED   │ extension/content.js:33                                 │
│ FR-E8: Extension Bearer Session Token Sync             │ COMPLETED   │ extension/options.js:14, popup.js:35                    │
│                                                        │             │                                                         │
│ Background Service Worker Navigation Interceptor       │ COMPLETED   │ extension/background.js:1                               │
│ Chrome Web Store Storefront Icons (16/48/128px)        │ COMPLETED   │ extension/icon16.png, icon48.png, icon128.png           │
│ Chrome Web Store Privacy Policy Document               │ COMPLETED   │ extension/privacy.html                                  │
│                                                        │             │                                                         │
│ FR-P1: Telemetry Health Endpoints                      │ COMPLETED   │ main.py:213 (/api/health & /api/v1/health)              │
│ FR-P2: Anonymous Sliding-Window IP Rate Limiting       │ COMPLETED   │ main.py:57 (check_ip_rate_limit)                        │
│ FR-P3: Persistent SQLite L1 Cache & History Storage    │ COMPLETED   │ db.py:1 (trustlens.db cache & history tables)           │
│ FR-P4: Dual Route Versioning (/api & /api/v1)          │ COMPLETED   │ main.py:214, 228, 264                                   │
│ FR-P5: Structured JSON Privacy-Safe Logging            │ COMPLETED   │ main.py:25 (no raw claims or URLs logged)               │
│                                                        │             │                                                         │
│ Automated Pytest Test Suite (15/15 Tests Passing)      │ COMPLETED   │ test_main.py (100% pass rate)                           │
│ Next.js 16 Turbopack Production Build                  │ COMPLETED   │ my-vibe-app/ (0 compilation errors)                     │
│ GitHub Actions CI/CD Pipeline                          │ COMPLETED   │ .github/workflows/ci.yml                                │
│ CodeRabbit Automated AI Review Configuration           │ COMPLETED   │ .coderabbit.yaml                                        │
│ Roo Code Nightly / Cline Workspace Configuration       │ COMPLETED   │ .clinerules, .roomodes, .vscode/settings.json           │
│ GSD Core v1.16.0 Framework & Planning Directory        │ COMPLETED   │ .agents/, .planning/                                    │
└────────────────────────────────────────────────────────┴─────────────┴─────────────────────────────────────────────────────────┘
```

---

### 2.2 Remaining Requirements (Milestone 2.0 Roadmap — In Planning)

```
┌────────────────────────────────────────────────────────┬─────────────┬─────────────────────────────────────────────────────────┐
│ Functional Requirement / Subsystem                     │ Status      │ Planned Target & Deliverables                           │
├────────────────────────────────────────────────────────┼─────────────┼─────────────────────────────────────────────────────────┤
│ FR-R1: Distributed Redis / Dragonfly L2 Caching        │ PLANNED     │ Distributed sub-millisecond cache & sliding rate limit  │
│ FR-R2: Cloud pgvector PostgreSQL Vector Scaling        │ PLANNED     │ Migrate in-memory cosine vectors to Supabase pgvector   │
│ FR-R3: Stripe Billing & Subscription Tier Gating       │ PLANNED     │ Free (20/day) vs Pro ($9/mo) vs Team ($29/mo) plans     │
│ FR-R4: Developer API Key Self-Service Provisioning     │ PLANNED     │ User dashboard API key generator & revocation tool      │
│ FR-R5: Multi-Tenant Quota & SLA Latency Enforcement    │ PLANNED     │ Per-tier rate limits, webhook alerts, priority queuing  │
│ FR-R6: Multi-Modal Claim Verification (Image/OCR)      │ PLANNED     │ Reverse image search, screenshot OCR & deepfake scan    │
│ FR-R7: Pre-Flight Web3 Wallet Transaction Simulation   │ PLANNED     │ Live EVM/Solana simulation of asset balances before sign│
│ FR-R8: Automated Chrome & Firefox Store CI Deployment  │ PLANNED     │ GitHub Actions automated store package build & publish  │
└────────────────────────────────────────────────────────┴─────────────┴─────────────────────────────────────────────────────────┘
```

---

## 3. System Architecture

```
                    ┌────────────────────────────────────────────────────────┐
                    │               Client & Presentation Tier               │
                    └────────────────────────────────────────────────────────┘
                       │                                    │
                       ▼                                    ▼
       ┌───────────────────────────────┐   ┌───────────────────────────────┐
       │   Chrome MV3 Extension        │   │   Next.js 16 Web Dashboard    │
       │   - In-page closed Shadow DOM │   │   - App Router (Turbopack)    │
       │   - Background Service Worker │   │   - Supabase SSR Auth         │
       │   - Navigation Interstitial   │   │   - Testing Workbench         │
       │   - Safe DOM (zero innerHTML) │   │   - Profile & Daily Metrics   │
       │   - Token Sync & Badging      │   │   - [M2.0] Stripe & API Keys  │
       └───────────────────────────────┘   └───────────────────────────────┘
                       │                                    │
                       └──────────────────┬─────────────────┘
                                          │
                                          ▼
                    ┌────────────────────────────────────────────────────────┐
                    │            Core Service Gateway (FastAPI)              │
                    │         main.py  (CORS, Logging, Rate Limiter)         │
                    └────────────────────────────────────────────────────────┘
                           │                  │               │
         ┌─────────────────┴────────┐         │               │
         ▼                          ▼         ▼               ▼
┌─────────────────────────┐ ┌─────────────┐ ┌───────────────┐ ┌──────────────────┐
│   Truth Engine          │ │Safety Engine│ │[M2.0] Vision  │ │  Supabase Auth   │
│   (claims_engine.py)    │ │(url_scanner)│ │& Multi-Modal  │ │  & PostgreSQL    │
│   - Google Fact Check   │ │-9 Heuristics│ │- Reverse Image│ │  - GoTrue JWT    │
│   - Hybrid BM25+Vectors │ │-Web Risk API│ │- Screenshot   │ │  - profiles table│
│   - NLI Stance Scoring  │ │-RDAP Age    │ │  OCR          │ │  - usage_daily   │
│   - Composite Truth     │ │-SSL Socket  │ │- Synthetic    │ │  - Row-Level Sec │
│   - Grounded Synthesis  │ │-Web3 Drainer│ │  Detection    │ │  - [M2.0] pgvector│
└─────────────────────────┘ └─────────────┘ └───────────────┘ └──────────────────┘
         │                          │                 │               │
         └─────────────────┬────────┴─────────────────┴───────────────┘
                           ▼
                    ┌────────────────────────────────────────────────────────┐
                    │              Persistence & Cache Layer                 │
                    │   - SQLite (trustlens.db): L1 local fast cache         │
                    │   - [M2.0] Redis / Dragonfly: Distributed L2 cache     │
                    │   - Sanitized audit history log (counts only)          │
                    └────────────────────────────────────────────────────────┘
```

---

## 4. API Specification & Contracts

### 4.1 Claim Verification (Implemented)
- **Endpoints**: `POST /api/verify` & `POST /api/v1/verify/claim`
- **Headers**:
  - `Content-Type: application/json`
  - `Authorization: Bearer <Supabase_JWT>` *(Optional; unauthenticated requests proceed with IP rate limit)*
- **Request Body**:
  ```json
  {
    "text": "Drinking colloidal silver cures viral infections."
  }
  ```
- **Response Body**:
  ```json
  {
    "claims": [
      {
        "claim": "Drinking colloidal silver cures viral infections.",
        "verdict": "False",
        "confidence": 0.92,
        "trust_score": 8.0,
        "stance": "Refutes",
        "synthesis": "According to Mayo Clinic & PolitiFact, this statement is rated False. Medical regulators confirm colloidal silver has no proven efficacy against viral pathogens.",
        "sources": [
          {
            "publisher": "Mayo Clinic & PolitiFact",
            "title": "Medical regulators confirm colloidal silver has no proven efficacy against viral pathogens.",
            "rating": "False",
            "url": "https://www.politifact.com/factchecks/2022/colloidal-silver-cure-myth/",
            "verdict": "False",
            "date": "2022-11-10"
          }
        ],
        "source": "hybrid_retrieval",
        "cached": false
      }
    ]
  }
  ```

### 4.2 URL Security Scanner (Implemented)
- **Endpoints**: `POST /api/scan` & `POST /api/v1/scan/url`
- **Request Body**:
  ```json
  {
    "url": "https://uniswap-v4-claim.airdrop-eth.xyz/permit2"
  }
  ```
- **Response Body**:
  ```json
  {
    "url": "https://uniswap-v4-claim.airdrop-eth.xyz/permit2",
    "level": "Dangerous",
    "threats": [],
    "flags": [
      "High-risk TLD",
      "Urgency / crypto-drainer keyword",
      "Crypto-drainer / wallet hijacking pattern detected"
    ],
    "flag_explanations": [
      {
        "flag": "High-risk TLD",
        "explanation": "Domain uses a top-level domain frequently associated with spam, bulletproof hosting, and phishing campaigns."
      },
      {
        "flag": "Crypto-drainer / wallet hijacking pattern detected",
        "explanation": "Detected deceptive wallet-connection signatures, permit2 approvals, or drainer patterns designed to steal tokens."
      }
    ],
    "telemetry": {
      "domain_age_days": 12,
      "ssl": { "valid": true, "issuer": "Let's Encrypt", "days_until_expiry": 82 },
      "should_block": true
    },
    "should_block": true,
    "source": "heuristics"
  }
  ```

### 4.3 Pre-Navigation Warning Interstitial (Implemented)
- **Endpoints**: `GET /api/interstitial?url={target_url}` & `GET /interstitial`
- **Response Body**:
  ```json
  {
    "title": "TrustLens Security Warning",
    "url": "https://suspicious-target.xyz",
    "warning": "CRITICAL RISK: TrustLens detected dangerous phishing or crypto-drainer signatures.",
    "action_required": "Do not enter passwords, private keys, or wallet seed phrases on this domain.",
    "can_proceed": true
  }
  ```

### 4.4 Multi-Modal Verification (Planned — Milestone 2.0)
- **Endpoint**: `POST /api/v1/verify/multimodal`
- **Input**: `{ "image_url": "...", "caption": "..." }` or multipart form data.
- **Output**: Reverse search matches, digital alteration confidence, and verified publisher fact-checks.

---

## 5. Security & Privacy Guarantees

1. **Zero Browsing History Storage**:
   - The platform never stores user claim text, visited URLs, or browsing histories.
   - Database tables store strictly aggregated numerical counts (`claim_checks`, `url_scans`).
2. **Strict DOM Protection**:
   - Chrome extension overlay is mounted inside `attachShadow({ mode: "closed" })` to ensure host page CSS cannot break or visually spoof verification pills.
   - All DOM operations strictly use `document.createElement` and `textContent`. String-to-HTML interpolation (`innerHTML`) is banned.
3. **Authentication Defense in Depth**:
   - Next.js server components and middleware use `supabase.auth.getUser()`, which validates cryptographically against the Supabase GoTrue auth server.
   - Open-redirect attacks (`?next=//evil.com`) are neutralized by `getSafeRedirectUrl`, which rejects protocol-relative and external URLs.
   - Generic login error messages prevent email enumeration attacks.
   - PostgreSQL Row-Level Security (RLS) guarantees users can only access their own profile and usage rows.

---

## 6. Automated Testing & Quality Assurance

### Pytest Test Suite (`test_main.py`)
- **Command**: `.venv\Scripts\python.exe -m pytest test_main.py -v`
- **Result**: **15 passed, 0 failed** (100% passing)
- **Coverage**:
  1. `test_health`: Telemetry status and live/demo mode.
  2. `test_health_versioned`: `/api/v1/health` route alias.
  3. `test_scan_flags_lookalike`: Phishing brand look-alike detection and flag explanations.
  4. `test_scan_invalid_url_rejected`: HTTP 400 rejection on malformed inputs (`FR-U4`).
  5. `test_scan_does_not_call_web_risk_without_separate_key`: Safety isolation for unmetered calls.
  6. `test_verify_returns_claims`: Claim structure and source tag inclusion (`FR-C4`).
  7. `test_verify_max_five_claims_cap`: Atomic claim splitting capped at 5 claims (`FR-C2`).
  8. `test_verify_no_evidence_found`: Explicit "No evidence found" handling (`FR-C5`).
  9. `test_versioned_routes`: Versioned alias contracts (`/api/v1/verify/claim`, `/api/v1/scan/url`).
  10. `test_anonymous_access_allowed`: Unauthenticated access supported via sliding-window IP rate limiting.
  11. `test_invalid_token_rejected`: HTTP 401 on tampered/expired Bearer tokens.
  12. `test_history_persistent`: SQLite persistent history retrieval (`FR-P3`).
  13. `test_phase2_hybrid_retrieval_and_stance`: Hybrid BM25/vector search, NLI stance, and grounded synthesis.
  14. `test_phase3_crypto_drainer_detection`: Crypto-drainer pattern detection and `should_block` flag.
  15. `test_phase3_interstitial_endpoint`: Pre-navigation warning interstitial endpoint contract (`FR-U8`).

### Next.js Production Compilation
- **Command**: `cmd.exe /c npm run build` (in `my-vibe-app/`)
- **Result**: Compiles cleanly with Turbopack, React 19, and TypeScript with zero errors.

---

## 7. Developer Tooling & Integrations

- **GitHub Actions CI/CD ([.github/workflows/ci.yml](file:///c:/Users/Saura/OneDrive/Desktop/TrusthLens/.github/workflows/ci.yml))**: Automated test and build verification running on all pulls and pushes to `main`.
- **CodeRabbit AI Code Review ([.coderabbit.yaml](file:///c:/Users/Saura/OneDrive/Desktop/TrusthLens/.coderabbit.yaml))**: Enforces security rules, safe DOM compliance, and path exclusions on all Pull Requests.
- **Roo Code Nightly / Cline ([.clinerules](file:///c:/Users/Saura/OneDrive/Desktop/TrusthLens/.clinerules), [.roomodes](file:///c:/Users/Saura/OneDrive/Desktop/TrusthLens/.roomodes), [.vscode/settings.json](file:///c:/Users/Saura/OneDrive/Desktop/TrusthLens/.vscode/settings.json))**: Configured with Google Gemini `gemini-2.0-flash` free tier model, architectural guidelines, and specialized agent modes.
- **GSD Core v1.16.0 Framework ([.planning/](file:///c:/Users/Saura/OneDrive/Desktop/TrusthLens/.planning/), [.agents/](file:///c:/Users/Saura/OneDrive/Desktop/TrusthLens/.agents/))**: Stamped brownfield codebase map, living state tracking, and spec-driven roadmap.
- **Specialist Agent Configuration ([trustlens-codebase.agent.md](file:///c:/Users/Saura/OneDrive/Desktop/TrusthLens/.github/agents/trustlens-codebase.agent.md))**: Custom agent profile with unrestricted IDE tool access for pair programming.
- **Git Remote Authorization**: Remote origin authenticated via GitHub Personal Access Token to `https://github.com/Programming-with-Abhinav/TrusthLens.git`.
