# TrustLens AI — Agent & Specification Hub

This directory contains the operational specifications, product requirement definitions (PRD), and specialized agent instruction prompts for the **TrustLens AI** dual-protection browser system.

## Directory Structure

- **`TrustLens_PRD_v1.1.md`**: Master Product Requirements Document (PRD Version 2.1). Defines core functional requirements (Phases 1 through 4), technical contracts, architecture guidelines, security rules, and performance budgets.
- **`trustlens-codebase.agent.md`**: Agent prompt configuration and context contract for AI coding assistants (Antigravity, Roo Code, Cline, CodeRabbit) operating on the TrustLens codebase.
- **`README.md`**: This guide describing the agent roles, specification boundaries, and development workflows.

## Core Architectural Boundaries

1. **Zero DOM Injections**: Under no circumstances should `innerHTML` or unchecked HTML interpolation be used in extension content scripts (`extension/content.js`), popup controllers (`extension/popup.js`), or web app components. Use `textContent` and `document.createElement`.
2. **Privacy Enforcement**: Backend logging (`main.py`) and SQLite/Supabase databases must hash or truncate inputs. Raw claim text and visited browsing URLs are never persisted in plain-text logs or stored on disk.
3. **Dual Route Compatibility**: All API routes are accessible via legacy (`/api/...`) and versioned (`/api/v1/...`) endpoints.
4. **Isolated Extension Overlays**: In-page verdict pills must always be isolated inside a closed Shadow DOM (`attachShadow({ mode: 'closed' })`) to prevent host site CSS collision and script tampering.
5. **Hybrid Intelligence**: Claim checking combines dense vector cosine similarity and BM25 with Reciprocal Rank Fusion (RRF), Natural Language Inference (NLI) stance classification, and temporal decay scoring.
