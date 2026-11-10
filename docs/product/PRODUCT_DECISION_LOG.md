# FashXStudio — Consolidated Product Decision Log

**Document ID:** `FASHX-DEC-002`  
**Version:** `1.0 — Approved Baseline`  
**Date:** `10 November 2026`  
**Status:** `Approved Governance Baseline`  
**Scope:** `Phase 01 — Product Architecture & Scope Decisions`  

---

## 1. Consolidated Decisions Register (PD-001 – PD-015)

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
| **PD-015** | Complete Phase 01 consolidated documentation baseline approved for exit gate. | **Approved Baseline** | Authorizes progression to Phase 02 repository consolidation. |

---

## 2. Decision Change & Scope Modification Policy

Following formal approval of the Phase 01 baseline:
1. Every scope modification requires filing a formal **MVP Change Request** under [docs/product/MVP_CHANGELOG.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/product/MVP_CHANGELOG.md).
2. P0 changes require written sign-off from the Product Owner / Founder.
3. Every added P0 requirement must specify concrete acceptance criteria and identify the equivalent P0 work being displaced.
4. Security, tenant isolation, and DPDP 2023 privacy requirements can never be compromised or deferred.
