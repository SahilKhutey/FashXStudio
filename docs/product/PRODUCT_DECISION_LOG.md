# FashXStudio — Consolidated Product Decision Log

**Document ID:** `FASHX-DEC-002`  
**Version:** `1.1 — Approved Governance Baseline`  
**Date:** `10 November 2026`  
**Status:** `Approved Governance Baseline`  
**Scope:** `Phase 01 — Product Architecture & Scope Decisions`  

---

## 1. Consolidated Decisions Register (PD-001 – PD-018)

| Decision ID | Core Architectural Decision | Status | Strategic Context & Reference |
| :--- | :--- | :--- | :--- |
| **PD-001** | Focus exclusively on personal-image VTO and authorized multi-brand discovery. | **Approved Baseline** | Sets core product identity; avoids generic price aggregation. |
| **PD-002** | Target urban and semi-urban Indian online fashion shoppers aged 18–35. | **Approved Baseline** | Geographic and demographic focus for Pilot MVP v1.0. |
| **PD-003** | Target Indian D2C apparel brands operating owned storefronts as first merchants. | **Approved Baseline** | Accessible decision-makers and direct catalog control. |
| **PD-004** | Adopt B2B2C architecture with merchant-first design partner commercial entry. | **Approved Baseline** | Merchants fund development; shoppers access free mobile discovery. |
| **PD-005** | Checkout remains external on merchant storefronts via outbound redirection. | **Approved Baseline** | Aligns with ADR-0001; eliminates in-app cart, payment, and order handling. |
| **PD-006** | Exactly 1 merchant design partner is sufficient for the first controlled pilot. | **Approved Baseline** | Prevents over-engineering multi-tenant enterprise tooling early. |
| **PD-007** | Ingest exactly 1 authorized catalog source (100–500 SKUs) for the pilot. | **Approved Baseline** | Controls operational overhead and validation cycles. |
| **PD-008** | Restrict initial categories to Men's T-shirts, shirts, and structured kurtas. | **Approved Baseline** | Excludes complex draping (sarees, lehengas) until V2. |
| **PD-009** | Hosted AI provider (FASHN API) required for production VTO inference. | **Approved Baseline** | Mock adapter barred from staging/production per ADR-0004. |
| **PD-010** | Custom foundation model training or local GPU clusters excluded from MVP. | **Approved Baseline** | Eliminates prohibitive early capital and infrastructure risk. |
| **PD-011** | Digital wardrobe supports saving, inspecting, and deleting completed looks. | **Approved Baseline** | Core retention hook; advanced outfit planning deferred to P2. |
| **PD-012** | Direct in-app cart, checkout, payments, inventory, and returns strictly frozen. | **Approved Baseline** | Non-destructive routing unmount enforced via config flags. |
| **PD-013** | Complete Phase 1.4 KPI framework and 14 pilot targets formally approved. | **Approved Baseline** | Mathematical definitions and measurement windows locked. |
| **PD-014** | Phase 1.3 MVP priority classification (P0, P1, P2) formally frozen. | **Approved Baseline** | P0 boundary locked; change request protocol enforced. |
| **PD-015** | Formal Phase 01 Exit Approval across all foundational product workstreams. | **Approved Baseline** | Unanimous Product Owner approval recorded; authorizes Phase 02. |
| **PD-016** | Reconcile ADR-0001 external checkout with B2B2C direct brand handoff. | **Approved Baseline** | Documented in ADR-0009; affiliate tracking optional, not mandatory. |
| **PD-017** | Reconcile VTO performance metrics into a dual-tier standard. | **Approved Baseline** | Tier 1 (Gate Ceilings $\le 45$s) vs Tier 2 (ADR-0004 Target $\le 30$s). |
| **PD-018** | Reconcile pre-pilot STATUS.md with historical prototype evaluation logs. | **Approved Baseline** | Phase 5 evaluation is historical benchmark; live accounts unexecuted. |

---

## 2. Key Formal Product Decisions & Governance Reconciliations

### PD-015 — Phase 01 Approval & Exit Gate Sign-Off
- **Status:** `APPROVED`
- **Date:** 10 November 2026
- **Decider:** Product Owner / Founder
- **Approved Decisions:**
  1. **Product Strategy & Target Market:** Focus on personal-image VTO and authorized multi-brand discovery for Indian shoppers aged 18–35 and Indian D2C apparel brands ([docs/product/PRODUCT_STRATEGY.md](PRODUCT_STRATEGY.md)).
  2. **Complete User Journeys:** End-to-end Shopper Journey (S01–S20) and Merchant Journey (M01–M15) with 12 critical journey recovery handlers ([docs/product/SHOPPER_JOURNEY.md](SHOPPER_JOURNEY.md), [docs/product/MERCHANT_JOURNEY.md](MERCHANT_JOURNEY.md)).
  3. **MVP Boundary & Priorities:** Phase 1.3 P0/P1/P2 classification locked, unmounting frozen commerce operations per ADR-0001 ([docs/product/MVP_SCOPE_AND_PRIORITY.md](MVP_SCOPE_AND_PRIORITY.md)).
  4. **Business Model Hypothesis:** Merchant-first B2B2C design partner commercial entry strategy ([docs/product/BUSINESS_MODEL_HYPOTHESIS.md](BUSINESS_MODEL_HYPOTHESIS.md)).
  5. **Validation Register:** Accept 12 product assumptions and 16 operational risks as initial validation register ([docs/product/ASSUMPTIONS_AND_RISKS.md](ASSUMPTIONS_AND_RISKS.md)).
  6. **KPI Framework:** Retain already-approved Phase 1.4 KPI framework (14 KPIs, formulas, non-interchangeable denominators, and Decision Gates G1–G8) ([docs/product/KPI_DEFINITIONS.md](KPI_DEFINITIONS.md), [docs/product/PILOT_SUCCESS_TARGETS.md](PILOT_SUCCESS_TARGETS.md)).
- **Founder Approval Comment:** *"Proceed with the proposed Phase 01 baseline."*
- **Phase 01 Exit Gate Verdict:** `APPROVED`.

---

### PD-016 — Commercial Model & Outbound Redirection Reconciliation (ADR-0001 Supplement)
- **Status:** `APPROVED`
- **Context:** Resolves the architectural distinction between [ADR-0001](../adr/0001-mvp-scope-and-repo-structure.md) (which cited affiliate link redirection) and the approved Phase 01 B2B2C strategy (which centers on direct merchant partnerships).
- **Resolution:** Formally documented in [ADR-0009](../adr/0009-merchant-first-b2b2c-and-checkout-handoff.md). Direct handoff to the authorized brand storefront PDP is the primary commerce integration. Affiliate network parameters (e.g. UTM tracking, network tokens) remain supported as optional metadata on outbound links, but affiliate network revenue is not a mandatory dependency for Pilot MVP success.

---

### PD-017 — Virtual Try-On Dual-Tier Performance Standard Reconciliation
- **Status:** `APPROVED`
- **Context:** Resolves the threshold variance between [ADR-0004](../adr/0004-tryon-provider.md) (provider evaluation: P95 latency $\le 30$s, completion $\ge 95\%$) and Phase 1.4 (pilot release contract: P95 latency $\le 45$s, completion $\ge 90\%$).
- **Resolution:** Formally establishes the dual-tier evaluation framework:
  1. **Tier 1 (Contractual Pilot Release Gate Ceiling — Phase 1.4 Baseline):**
     - P95 submit-to-image latency $\le 45.0$ seconds.
     - Try-on job completion rate $\ge 90.0\%$.
     - Inference pipeline defect rate $\le 15.0\%$.
     - Visual realism & garment preservation score $\ge 3.80 / 5.0$.
  2. **Tier 2 (Operational Excellence Target — ADR-0004 Provider Qualification):**
     - P95 submit-to-image latency $\le 30.0$ seconds.
     - Try-on job completion rate $\ge 95.0\%$.
     - Inference pipeline defect rate $\le 10.0\%$.
     - Visual realism & garment preservation score $\ge 4.00 / 5.0$.
- **Consequence:** Both tiers are measured and reported by `scripts/rc13/evaluate_vto.py` and documented in [docs/vto/VTO_METRICS.md](../vto/VTO_METRICS.md).

---

### PD-018 — Pre-Pilot Status & Evaluation Provenance Reconciliation
- **Status:** `APPROVED`
- **Context:** Clarifies the relationship between the historical VTO evaluation report ([docs/logs/phase5-eval-2026-10-10.md](../logs/phase5-eval-2026-10-10.md), reporting 80 evaluated jobs) and the honest status in [docs/STATUS.md](../STATUS.md) (stating no live vendor account or real images verified).
- **Resolution:** The Phase 5 evaluation report represents historical pre-registration benchmark data gathered during prototype sandbox trials prior to the 2026-10-24 Reality Reset ([AGENTS.md](../../AGENTS.md)). Per repo governance rules:
  - No live vendor API key or paid GPU runs are active in current CI or local environments.
  - No simulated evidence is treated as definitive production validation.
  - Pre-pilot status is strictly maintained in [docs/STATUS.md](../STATUS.md) and [docs/provenance.md](../provenance.md) until live physical evidence cards are executed and written by the founder under `docs/evidence/`.

---

## 3. Decision Change & Scope Modification Policy

Following formal approval of the Phase 01 baseline:
1. Every scope modification requires filing a formal **MVP Change Request** under [docs/product/MVP_CHANGELOG.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/product/MVP_CHANGELOG.md).
2. P0 changes require written sign-off from the Product Owner / Founder.
3. Every added P0 requirement must specify concrete acceptance criteria and identify the equivalent P0 work being displaced.
4. Security, tenant isolation, and DPDP 2023 privacy requirements can never be compromised or deferred.
