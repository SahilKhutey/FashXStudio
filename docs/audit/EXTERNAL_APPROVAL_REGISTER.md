# FashXStudio — Phase 02.4: External Approval & Blocker Register

**Document ID:** `FASHX-AUD-009`  
**Phase:** 02.4 — Audit Mock Versus Real Integrations (Execution E)  
**Date:** 2026-11-11  
**Author:** Antigravity Agent (Auditor)  
**Status:** COMPLETE (Audited Baseline)  
**Branch:** `recovery/rc13.1-governance-correction`  

---

## 1. Executive Summary

Connecting external cloud services, AI model providers, and partner merchant feeds requires formal commercial, legal, and architectural clearance before production deployment. In accordance with `AGENTS.md` **Rule 7** (no external data transmission or dependency addition without explicit authorization) and **ADR 0005** (no unauthorized scraping), this register enumerates all external dependencies and their requisite approvals.

---

## 2. External Dependency Approval Register

| Dependency | Category | Current Status | Required Approval & Documentation | Blocker for MVP? | Responsible Owner |
|:---|:---|:---:|:---|:---:|:---:|
| **FASHN Hosted VTO** | AI Try-On Provider | `LOCAL` | Commercial API account agreement, data processing addendum (DPA) permitting AI biometric processing, billing setup ($0.075/run estimate), and production API key | **YES (P0)** | Founder / Tech Lead |
| **Anthropic Claude VLM** | Multimodal Enrichment | `LOCAL` | Commercial API key, model usage terms, rate limit quota ($10.00/day budget cap) | **YES (P1)** | Tech Lead |
| **AWS S3 / Cloudflare R2** | Cloud Object Storage | `LOCAL` | Cloud account, dedicated media bucket creation, IAM policy configuration, S3v4 signing, and CORS display policy | **YES (P0)** | DevOps / Tech Lead |
| **External JWKS IdP (Supabase/Auth0)** | Identity Provider | `LOCAL` | Hosted auth tenant, issuer/audience verification, public JWKS endpoint reachability, user registration flow | **YES (P0)** | Tech Lead |
| **Direct Pilot Merchant Feed** | Product Catalog | `LOCAL` | Written bilateral pilot agreement granting: (1) product metadata rights, (2) thumbnail display rights, (3) explicit AI virtual try-on processing rights, (4) takedown procedure | **YES (P0)** | Founder / Business |
| **Managed PostgreSQL 16** | Relational Database | `LOCAL` | Cloud DB instance provisioned with `pgvector` extension enabled, SSL enforcement, and automated point-in-time recovery | **YES (P0)** | DevOps / Tech Lead |
| **Managed Redis 7** | Cache & Session Store | `LOCAL` | Cloud Redis instance with TLS authentication, memory eviction policy, and connection pool sizing | **YES (P0)** | DevOps / Tech Lead |
| **Amazon / Flipkart Affiliate** | Catalog Syndication | `LOCAL` | Affiliate program approval, written compliance with ToS prohibiting scraping, API access credentials | NO (Post-MVP) | Business |
| **Stripe / Razorpay** | Payment Gateway | `MOCK` | Not required for initial MVP (per ADR 0009 merchant checkout handoff) | NO | Product Owner |
| **Shiprocket / Delhivery** | Logistics / Shipping | `MOCK` | Not required for initial MVP (per ADR 0009 merchant checkout handoff) | NO | Product Owner |

---

## 3. Catalog Rights & Sourcing Protocol

In accordance with **ADR 0005** (`docs/adr/0005-catalog-sourcing.md`) and **ADR 0009** (`docs/adr/0009-merchant-first-b2b2c-and-checkout-handoff.md`):

1. **Dual-Rights Requirement:** Every ingested product source must explicitly register two boolean permissions in `database.models.catalog.CatalogSource`:
   - `rights_display: bool` — Right to render the garment image in search, recommendation feeds, and product detail screens.
   - `rights_tryon: bool` — Explicit permission to pass garment images into AI try-on diffusion models.
2. **Scraping Prohibition:** Scraping public e-commerce websites without written authorization violates repository policy. All catalog acquisition must proceed through direct brand feeds (`PartnerFeedAdapter`) or approved affiliate feeds.
3. **Synthetic Seed Quarantine:** Seed datasets (`data/catalog/curated-seed-catalog.csv`) are strictly restricted to local development and must remain in `suspended` status.
