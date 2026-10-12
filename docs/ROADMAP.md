# FashXStudio: Program Master Roadmap (Phases 0 – 13)

- **Product:** FashXStudio — AI Fit Intelligence & Size-Return Reduction Engine for Indian Fashion Brands
- **Current Lifecycle Stage:** Phase 12 Cleared $\to$ **Phase 13: Commercial Scale-Out**
- **Last Updated:** October 2026
- **Current Milestone Tag:** `v1.1-gate2`

---

## 1. Program Phase Overview & Trajectory

```
Phase 0: Baseline & Repository Audit (Oct 2026) ────────────────────────── [Tag: v0.0-baseline]
  ↳ Ground-truth audit of dependencies, licenses, mock code, and debt

Phase 1: Honest Documentation & Restructure (Oct 2026) ─────────────────── [Tag: v0.1-docs]
  ↳ Single source of truth, elimination of fake metrics and synthetic claims

Phase 2: Codebase Unification & Package Hygiene (Oct 2026) ─────────────── [Tag: v0.2-unified]
  ↳ Elimination of duplicate app roots; canonical backend/fashx package

Phase 3: Security & Auth Spine (Oct 2026) ──────────────────────────────── [Tag: v0.3-auth]
  ↳ Default-deny API gateway, JWT verification, tenant/user ownership scopes

Phase 4: Persistence, Database & S3 Storage (Oct 2026) ─────────────────── [Tag: v0.4-persistence]
  ↳ PostgreSQL + pgvector schemas, Alembic migrations, signed S3 URLs

Phase 5: Real Try-On Inference Pipeline (Oct 2026) ─────────────────────── [Tag: v0.5-tryon]
  ↳ Commercial FASHN API adapter, Monk skin tone fairness, quality gates

Phase 6: Real Catalog Ingestion & Normalization (Oct 2026) ─────────────── [Tag: v0.6-catalog]
  ↳ Google Merchant XML/CSV parsers, dHash deduplication, takedown CLI

Phase 7: Real Discovery Feed & Constrained MMR (Oct 2026) ──────────────── [Tag: v0.7-discovery]
  ↳ 11-feature vector scoring, diversity ranking, feed exclusion rules

Phase 8: Mobile MVP — iOS & Android (Oct 2026) ─────────────────────────── [Tag: v0.8-mobile-mvp]
  ↳ Expo SDK 57 / React Native 0.86 New Architecture, camera quality gate

Phase 9: Security Hardening, DPDP & Release Gates (Oct 2026) ───────────── [Tag: v0.9-pilot-ready]
  ↳ DPDP cascading erasure, 365-day CERT-In log compliance, breach drill

Phase 10: Closed Pilot Execution & G6 Verdict (Oct 2026) ───────────────── [Tag: v0.10-pilot-complete]
  ↳ 38 activated participants, 4.12/5.0 realism rating, 68.4% W2 return

Phase 11: Strategic Evaluation & Path B Selection (Oct 2026) ───────────── [Tag: v1.0-decision]
  ↳ Scorecard: Path B won (435/500); B2B return reduction engine chosen

Phase 12: Operate, Learn & Scale — The First 90 Days (Oct 2026) ────────── [Tag: v1.1-gate2]
  ↳ PR 12A: Operating Foundation, SLOs, deterministic experiments
  ↳ PR 12B: B2B multi-tenant backend, <45KB Shadow DOM storefront widget
  ↳ PR 12C: Gate 2 Evaluation (Verdict: SCALE: 5 brands, 3.4 pts return cut)

Phase 13: Commercial Scale-Out & Institutional Seed (Nov 2026 – Q2 2027) ── [ACTIVE]
  ↳ Public Shopify App Store listing, GPU HPA autoscaling, ₹4.0 Cr Seed Round
```

---

## 2. Phase-by-Phase Milestone Summary

| Phase | Core Objective | Key Deliverables | Verification / Status |
|---|---|---|---|
| **Phase 0** | Codebase Audit | Repository audit, dependency lock, license audit | Complete (`v0.0-baseline`) |
| **Phase 1** | Docs Restructure | Honest STATUS.md, architecture RFCs, rule index | Complete (`v0.1-docs`) |
| **Phase 2** | Code Hygiene | Unified `backend/fashx/`, removed legacy directories | Complete (`v0.2-unified`) |
| **Phase 3** | Auth Spine | Default-deny middleware, JWT verification, RBAC | Complete (`v0.3-auth`) |
| **Phase 4** | Real Storage | PostgreSQL, MinIO/S3 signed capability URLs | Complete (`v0.4-persistence`) |
| **Phase 5** | Try-On Engine | FASHN adapter, Monk skin tone calibrator, C2PA watermark | Complete (`v0.5-tryon`) |
| **Phase 6** | Real Catalog | XML/CSV merchant parsers, dHash deduplication | Complete (`v0.6-catalog`) |
| **Phase 7** | Discovery Feed | Constrained MMR ranker, 11-feature personalization | Complete (`v0.7-discovery`) |
| **Phase 8** | Mobile MVP | Expo SDK 57 iOS/Android app, quality gate camera | Complete (`v0.8-mobile-mvp`) |
| **Phase 9** | Hardening & DPDP | Cascading erasure, outside legal sign-off, release gates | Complete (`v0.9-pilot-ready`) |
| **Phase 10** | Closed Pilot | 38 testers, pre-registered plan, G6 verdict memo | Complete (`v0.10-pilot-complete`) |
| **Phase 11** | Strategy & Decision | 5-way scorecard (Path B won 435/500), 90-day plan | Complete (`v1.0-decision`) |
| **Phase 12** | 90-Day Execution | PR 12A Foundation, PR 12B B2B Platform, PR 12C Gate 2 | **Complete (`v1.1-gate2`)** |
| **Phase 13** | Commercial Scale | Shopify App listing, Seed Round (₹4 Cr), 50+ brands | **ACTIVE (In Progress)** |

---

## 3. Phase 13 Workstreams: Commercial Scale-Out

Following the **SCALE** verdict at Gate 2, execution focuses on three core pillars:

### Pillar 1: Self-Serve Product & Shopify App Store Listing (Nov – Dec 2026)
- **Shopify App Store Submission:** Package `fashx-widget.js` into an official Shopify Public App with automated billing integration (`Shopify App Subscription API`).
- **One-Click Theme App Extension:** Merchants install with zero code pasting directly from the Shopify App Store.
- **Automated Size Chart Parser:** OCR-based parser that imports merchant PDF/JPEG size charts and converts them to structured JSON.

### Pillar 2: Scalable Compute & Infrastructure Hardening (Dec 2026 – Jan 2027)
- **KEDA Event-Driven Worker Pool:** Spot GPU instances autoscaling on Redis queue depth ($> 15$ jobs).
- **Sub-Second Preview Engine:** Distilled latent diffusion checkpoint reducing try-on generation latency from 9.8s to $< 4.5\text{s}$.
- **Postgres Read Replicas:** Complete traffic segregation between merchant analytics and shopper widget sessions.

### Pillar 3: Capital & Enterprise Growth (Jan – Mar 2027)
- **Seed Fundraising Close:** Close ₹3.50 Cr – ₹5.00 Cr seed round led by early-stage institutional VC (Blume / Surge / Chiratae).
- **Startup India Grant Disbursement:** Receive ₹50 Lakh non-dilutive SISFS grant.
- **Target Scale:** 50 live partner brands, ₹12,00,000 monthly recurring revenue ($1.44\text{ Cr ARR}$).
