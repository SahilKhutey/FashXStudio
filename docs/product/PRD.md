# FashXStudio — Product Requirements Document (PRD)

**Document ID:** `FASHX-PRD-001`  
**Version:** `1.0 — Approved Baseline`  
**Date:** `10 November 2026`  
**Status:** `Approved by Product Owner`  
**Scope:** `Phase 01 — Core Product Requirements Baseline`  

---

## 1. Product Overview & Purpose

The FashXStudio Pilot MVP is an AI-powered fashion discovery, personalization, and virtual try-on platform. It connects authorized Indian D2C apparel brands with online shoppers aged 18–35 to reduce visual appearance and fit uncertainty before purchase.

### Core Product Capabilities
1. **Shopper Profile & Privacy:** Minimum viable profile creation with granular, purpose-specific DPDP Act 2023 consent capture.
2. **Authorized Catalog Pipeline:** Ingestion, normalization, and quality validation of 100–500 upper-body SKUs from a design partner merchant.
3. **Discovery & Inspection:** Multi-brand catalog feed, keyword/filter search, and interactive Product Detail Pages (PDP) with real-time VTO eligibility indicators.
4. **Asynchronous Virtual Try-On:** Diffusion-powered try-on using the shopper's uploaded photo and merchant garment imagery via a hosted AI provider (FASHN).
5. **Wardrobe & Commerce Handoff:** Persisting styled looks to a digital closet and providing server-controlled outbound redirection to the merchant's store.

---

## 2. User Roles & System Responsibilities

| Role | Description & Primary Responsibilities |
| :--- | :--- |
| **Shopper** | End-consumer who browses garments, uploads photos under explicit consent, generates virtual try-ons, saves looks, and redirects to merchant stores. |
| **Merchant Administrator** | Brand executive who executes pilot agreements, authorizes data/image licenses, and reviews engagement metrics. |
| **Merchant Operator** | Catalog manager who connects feeds/CSVs, fixes validation errors, and approves products for publication. |
| **FashXStudio Administrator** | Internal operator managing tenant verification, provider spend limits, queue monitoring, and quality benchmarks. |
| **System Services** | Background workers executing feed ingestion, normalization, vector indexing, image validation, GPU inference, and analytics aggregation. |

---

## 3. Functional Requirements (FR-001 – FR-020)

| Requirement ID | Capability Description | Priority | Parent Subsystem |
| :--- | :--- | :--- | :--- |
| **FR-001** | Shopper registration, login, logout, and stateless JWT session management. | **P0** | Authentication |
| **FR-002** | Granular, purpose-specific DPDP 2023 consent capture with full revocation and deletion workflows. | **P0** | Privacy & Security |
| **FR-003** | Progressive minimum viable profile creation (style preferences, usual size range). | **P0** | Shopper Profile |
| **FR-004** | Ingestion of authorized product data from CSV, JSON feed, or Shopify connector. | **P0** | Catalog Acquisition |
| **FR-005** | Schema normalization, attribute tagging, deduplication, and quality validation gates. | **P0** | Catalog Governance |
| **FR-006** | Multi-brand product feed, category browsing, keyword search, and price/size filtering. | **P0** | Discovery & Search |
| **FR-007** | Product Detail Page with image gallery, size chart modal, and VTO eligibility status. | **P0** | Discovery & Search |
| **FR-008** | Client and server-side photo validation (format, resolution, single human, pose, lighting). | **P0** | Virtual Try-On |
| **FR-009** | Hosted diffusion model inference integration (FASHN API) using authentic assets. | **P0** | Virtual Try-On |
| **FR-010** | Asynchronous VTO job state machine with queue tracking and client idempotency keys. | **P0** | Virtual Try-On |
| **FR-011** | High-fidelity result rendering with before/after interactive comparison slider. | **P0** | Virtual Try-On |
| **FR-012** | Recoverable error handling with user-actionable guidance and maximum 1 automated retry. | **P0** | Virtual Try-On |
| **FR-013** | Digital wardrobe persistence allowing shoppers to save, inspect, and delete generated looks. | **P0** | Digital Wardrobe |
| **FR-014** | Server-controlled outbound merchant redirect logging purchase intent and click tracking. | **P0** | Commerce Handoff |
| **FR-015** | Universal event logging for core conversion funnel telemetry without collecting PII. | **P0** | Analytics |
| **FR-016** | Structured post-try-on quality feedback collection (1–5 star rating and issue tags). | **P0** | Feedback Engine |
| **FR-017** | Merchant onboarding, legal agreement execution, and decoupled data/image permission grants. | **P0** | Merchant Platform |
| **FR-018** | Self-service merchant analytics dashboard and exportable CSV reports. | **P1** | Merchant Platform |
| **FR-019** | Vector-based personalized recommendation ranking and style quiz refinement. | **P1** | Discovery & Search |
| **FR-020** | Advanced wardrobe features (collections, outfit combinations, packing lists). | **P2** | Digital Wardrobe |

---

## 4. Non-Functional Requirements (NFRs)

| NFR Domain | Specific Engineering Requirement |
| :--- | :--- |
| **Security** | TLS 1.3 encryption in transit; AES-256 encryption at rest; strict multi-tenant isolation preventing cross-merchant catalog or analytics leaks. |
| **Privacy & DPDP** | Explicit consent capture before image processing; automated 24-hour buffer / 30-day retention policies; verifiable cryptographic erasure logging. |
| **Reliability** | Asynchronous Celery/Redis queue handling worker disconnects; durable PostgreSQL job lifecycle tracking; zero unhandled 500 exceptions. |
| **Performance** | API gateway p95 latency $< 500$ms (non-AI); catalog search p95 $< 800$ms; end-to-end VTO turnaround p95 $< 45$ seconds. |
| **Cost Governance** | Direct variable cost per try-on $C_{\text{VTO}} \le ₹12.00$; daily GPU provider spend ceiling capped at ₹5,000 on staging/pilot. |
| **Observability** | Structured JSON logging with `trace_id` correlation across API, queue, and worker tiers; real-time failure alerts. |
| **Compatibility** | Expo React Native app validated on Android 10+ and iOS 15+ devices; responsive web merchant portal on modern Chromium and WebKit. |

---

## 5. Architectural Boundaries & Product Constraints

1. **One Design Partner Merchant:** The pilot requires exactly one verified D2C brand partner supplying 100–500 active upper-body SKUs.
2. **Hosted Provider Default:** Production VTO inference is delivered via commercial hosted API (FASHN); custom foundation model training is strictly out of scope.
3. **Zero Commerce Liability:** FashXStudio **does not operate a shopping cart, payment gateway, order management, or returns infrastructure**. Checkout occurs exclusively on the merchant's external website.
4. **No False Fit Guarantees:** Virtual try-on is an appearance simulation. Physical fit predictions are explicitly disclaimed.
