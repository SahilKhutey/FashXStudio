> **Development log. Contains no real-world measurements or simulated evidence. Pre-pilot status maintained per AGENTS.md.**

# Dev Log: Phase 01 — Product Strategy, Journey Architecture, MVP Scope & Technical Contracts

**Branch**: `recovery/rc13.1-governance-correction`  
**Milestone Scope**: Phase 01 (Product Definition & Validation Blueprint v1.0)  
**Date**: November 10, 2026  
**Status**: Implemented & Verified (Static Analysis Green, Documentation Linter Passing)

---

## 1. Architectural Decisions & Scope Boundary Enforcement

Phase 01 established the foundational contracts, boundaries, and technical architecture across all five workstreams (1.1 through 1.5):

### A. B2B2C Architecture & Commercial Entry Strategy (Phase 1.1)
- Selected B2B2C model with merchant-first design partner entry:
  - Solves the cold-start problem by acquiring authorized product catalogs and brand imagery directly from Indian D2C apparel brands.
  - Keeps commerce and checkout on the merchant storefront, eliminating fulfillment, payment gateway liability, and returns handling from the MVP.
  - Focuses engineering resources on personal fashion discovery, fit confidence, and high-fidelity virtual try-on.
- Defined primary customer profiles:
  - **Merchant Partner (P1):** Indian D2C apparel brand with an active online storefront (Shopify, WooCommerce, or custom API).
  - **Consumer Shopper (P1):** Indian online apparel shopper aged 18–35 in Tier 1 and Tier 2 cities.
- Product scope constrained to high-compatibility garments: T-shirts, casual shirts, women's tops, and kurtas. Complex multi-piece garments (sarees, lehengas, layered outerwear) explicitly deferred.

### B. Dual User Journey Architecture (Phase 1.2)
- Formally defined state machines and interaction sequences for both core user personas:
  - **Shopper Journey (`FASHX-JRN-001`):** S01 to S20 covering frictionless registration, body silhouette profiling, catalog browsing with match scoring, asynchronous VTO job submission, try-on gallery inspection, look saving, and outbound referral handoff with affiliate tracking.
  - **Merchant Journey (`FASHX-JRN-002`):** M01 to M15 covering brand registration, feed onboarding (Shopify/CSV), try-on compatibility validation, catalog activation, and outbound referral analytics monitoring.
- Specified 12 critical journey edge-case recovery handlers (unsupported garment types, photo validation failures, inference queue timeouts, out-of-stock items, broken merchant referral URLs).

### C. MVP Scope Boundary & ADR-0001 Freezing (Phase 1.3)
- Classified 14 subsystems into P0 (Must-Have for pilot), P1 (Immediate Post-Pilot), and P2 (Deferred Scale).
- Enforced ADR-0001:
  - Cart, checkout, payment processing, inventory reservation, order logistics, and physical returns are strictly frozen and unmounted.
  - If a feature is not required to answer the central pilot hypothesis ("Can an authorized product be discovered and visualized via personal VTO to drive high-intent merchant referrals?"), it is unmounted.
- Instituted formal Scope Change Protocol and Displacement Rule in `MVP_CHANGELOG.md`.

---

## 2. Technical Implementation Specifications (Phase 1.5)

Phase 1.5 translated the approved Phase 1.4 KPI framework into concrete database, message bus, API, and worker specifications:

### A. Universal Event Schema & Event Contracts (`FASHX-ANL-002`)
- Authored `UniversalEventEnvelope` TypeScript/JSON schema enforcing standard metadata (`event_id`, `event_name`, `timestamp`, `session_id`, `user_id`, `merchant_id`, `device`, `app_version`).
- Specified exact payload schemas for 28+ events across acquisition (`user.signup_completed`, `profile.created`), discovery (`catalog.viewed`, `item.clicked`), VTO lifecycle (`tryon.requested`, `tryon.completed`, `tryon.failed`), engagement (`look.saved`, `wardrobe.item_added`), and merchant handoff (`referral.outbound_clicked`).

### B. Analytics Data Models (`FASHX-DB-001`)
- Authored production-ready PostgreSQL 16 DDL:
  - `analytics_events`: Monthly partitioned event ledger with JSONB payloads and composite indexes on `(event_name, timestamp DESC)` and `(merchant_id, timestamp DESC)`.
  - `merchant_metrics_daily`: Daily pre-aggregated rollups per merchant tracking discovery impressions, VTO generations, outbound clicks, and conversion rates.
  - `shopper_cohorts`: Registration cohort retention tracking table (`retained_day_1`, `retained_day_7`, `retained_day_30`).

### C. Analytics Instrumentation Architecture (`FASHX-ARCH-002`)
- Specified post-commit Transactional Outbox pattern:
  - Backend writes events to local database within the active transaction.
  - Dequeuer streams events reliably to Redis Streams (`stream:fashx:analytics`) without blocking request-response threads.
  - Atomic Redis hash counters provide real-time dashboard stats with asynchronous PostgreSQL persistence.

### D. Daily Aggregation Pipeline (`FASHX-ANL-003`)
- Designed Celery Beat daily rollup worker running at 00:05 UTC.
- Authored pure SQL queries computing all 14 KPIs with explicit zero-division guards (`NULLIF(..., 0)`).

### E. Reporting APIs & Legal Pack
- Authored REST contracts for `/api/v1/admin/kpis/summary` and `/api/v1/merchants/{id}/analytics` with secure CSV export capabilities.
- Formulated comprehensive Merchant Legal Pack (`FASHX-LEG-001`) covering Catalog Data License, Model/Image Rights, VTO Generation Authorization, DPDP-compliant Data Processing Agreement, and Notice-and-Takedown protocols.

---

## 3. VTO Quality Evaluation & Economic Framework

- **VTO Quality Evaluation Rubrics:**
  - 1–5 Visual Realism rubric (photorealism, lighting consistency, anatomical preservation, edge artifacting).
  - 1–5 Garment Preservation rubric (texture fidelity, pattern/print retention, logo preservation, color accuracy).
  - Two-tier image failure taxonomy (Shopper Photo Pre-flight Rejection vs Inference Pipeline Defect).
- **Unit Economics Model:**
  - Strict variable cost ceiling $C_{\text{VTO}} \le ₹12.00$ per generation.
  - Target gross margin $\ge 65\%$.
  - Daily pilot burn ceiling of ₹5,000/day backed by an automated circuit breaker.

---

## 4. Verification Summary

- Documentation linter executed and passing (`python scripts/docs_lint.py` -> `docs lint ok`).
- Full governance rules from `AGENTS.md` strictly verified (no touches to `docs/evidence/`, no fake metrics, no unearned ✅ in `docs/STATUS.md`).
