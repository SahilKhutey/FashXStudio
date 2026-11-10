# FashXStudio — Merchant Pilot Legal & Authorization Pack

**Document ID:** `FASHX-LEG-001`  
**Version:** `1.0 — Execution Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.3 — B2B Merchant Pilot Legal Framework`  

---

## 1. Executive Summary & Purpose

Before a merchant's proprietary catalog data or copyrighted product imagery can be ingested, stored, processed by diffusion AI models, or displayed in FashXStudio, a binding legal framework must be executed. 

Public availability of a product on an e-commerce website does **not** grant legal permission to scrape assets or submit them to third-party generative AI services. This document set defines the required contractual instruments.

---

## 2. Agreement Pack Inventory

The controlled pilot agreement pack consists of eight essential modules:

```
docs/legal/merchant-pilot/
├── README.md (This Document)
├── MERCHANT_PILOT_AGREEMENT.md (Master Commercial & Operational Terms)
├── PRODUCT_DATA_LICENSE.md (Metadata Ingestion & Display License)
├── PRODUCT_IMAGE_USAGE_PERMISSION.md (Copyright Clearance for Storage & Display)
├── VTO_PROCESSING_AUTHORIZATION.md (Explicit Generative AI Inference Authorization)
├── DATA_PROCESSING_AGREEMENT.md (DPDP Act 2023 Compliant Processor Terms)
├── ANALYTICS_AND_ATTRIBUTION_TERMS.md (Outbound Click Tracking & Data Aggregation)
├── PRODUCT_TAKEDOWN_PROCESS.md (SLA & Protocol for Revocation and Takedowns)
└── MERCHANT_ONBOARDING_CHECKLIST.md (Step-by-Step Legal Execution Checklist)
```

### Relationship to Existing Repository Legal Templates
This pack formalizes and extends the foundational legal drafts established in `docs/legal/`:
- Integrates Master Terms from [docs/legal/pilot-terms.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/legal/pilot-terms.md).
- Adopts Data Processor clauses from [docs/legal/brand-dpa-template.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/legal/brand-dpa-template.md).
- Adheres to the Privacy Policy baseline in [docs/legal/privacy-policy.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/legal/privacy-policy.md).

---

## 3. Scope of Authorizations

| Instrument | Granted Scope | Prohibited Scope |
| :--- | :--- | :--- |
| **Data License** | Ingest titles, prices, SKUs, descriptions, and size charts to render product cards. | Reselling or sublicensing raw merchant catalog data to third parties. |
| **Image Usage** | Cache garment photos in CDN and object storage for discovery display. | Using merchant garment photos for unrelated advertising or stock photography. |
| **VTO Authorization** | Submit front-facing garment photos to diffusion models (e.g. FASHN API) for shopper try-on. | Using merchant images to train proprietary open-weights foundation models without royalty agreements. |
| **Attribution Terms** | Track anonymous outbound click events (`fashx_click_id`) to evaluate purchase intent. | Injecting hidden tracking scripts or harvesting merchant customer PII. |
| **Takedown SLA** | Merchant can revoke permissions or delist SKUs with immediate effect ($\le 24$h SLA). | Continuing to generate try-ons for revoked or discontinued garments. |

---

## 4. Mandatory Pilot Launch Gate

A merchant's product catalog **must never be activated in the production discovery feed** until all items in this gate are verified by the human founder:

- [ ] **Entity Verification:** Legal business name, GSTIN, and authorized signatory identity confirmed.
- [ ] **Contract Execution:** Master Pilot Agreement signed by authorized officer.
- [ ] **Explicit Image Rights:** Brand confirms full commercial ownership or license to use studio imagery for AI processing.
- [ ] **DPA Execution:** Data Processing Agreement executed covering Indian DPDP 2023 obligations.
- [ ] **Approved Categories:** Scope restricted strictly to MVP upper-body categories (T-shirts, shirts, kurtas).
- [ ] **Verified Destination:** Outbound product URLs verified against merchant's registered domain allowlist.
- [ ] **Takedown Contact:** Operational emergency email established for immediate catalog pauses.
