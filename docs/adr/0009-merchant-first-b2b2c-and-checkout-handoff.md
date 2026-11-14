# ADR-0009: Merchant-First B2B2C Commercial Architecture and External Checkout Handoff

- **Status:** Accepted
- **Date:** 2026-11-10
- **Owner:** Sahil Khutey
- **Supersedes / Supplements:** Supplements [ADR-0001](0001-mvp-scope-and-repo-structure.md) and aligns with [ADR-0005](0005-catalog-sourcing.md)

---

## 1. Context

[ADR-0001](0001-mvp-scope-and-repo-structure.md) (accepted 2026-10-04) established the foundational unmounting of internal commerce systems (inventory, cart, checkout, payments, fulfillment, and returns) to focus development on personal virtual try-on and product discovery. ADR-0001 described outbound shopper redirection via third-party affiliate networks.

Concurrently, [ADR-0005](0005-catalog-sourcing.md) established that raw product feeds and high-resolution garment imagery must be acquired through authorized direct brand partnerships (Indian D2C apparel brands) rather than scraping or restricted affiliate networks, due to intellectual property, derivative works, and model training restrictions.

With the formal product-owner approval of the **Phase 01 Product Strategy (`FASHX-PROD-001`)** and **Business Model Hypothesis (`FASHX-BIZ-001`)**, FashXStudio has adopted a **B2B2C fashion technology platform model** with a merchant-first design partner entry strategy. This ADR reconciles the commercial handoff mechanism between ADR-0001, ADR-0005, and the approved Phase 01 baseline.

---

## 2. Architectural Decisions

1. **Direct Brand Product-Page Handoff as Primary Commerce Interface:**
   - The primary commercial transition from FashXStudio to commerce is an outbound handoff to the authorized merchant's owned storefront Product Detail Page (PDP) via deep links (`brand_redirect_url`).
   - The shopper completes sizing selection, carting, payment, and checkout entirely on the merchant's storefront. FashXStudio does not collect credit cards, store shipping addresses, or hold payment liabilities.

2. **Affiliate Parameters as Optional Metadata:**
   - Outbound referral URLs support affiliate network query parameters (e.g. `utm_source=fashx`, `aff_sub`, `click_id`) as optional metadata rather than a mandatory MVP business requirement.
   - Commercial monetization for the pilot is driven primarily by B2B design partner fees, pilot SaaS subscriptions, and usage-based try-on fees, with affiliate commissions functioning strictly as supplemental upside.

3. **Merchant Feed Ingestion & Try-On Authorization:**
   - Sourced products must carry verified written try-on authorizations per ADR-0005 and the Merchant Legal Pack (`docs/legal/merchant-pilot/README.md`).
   - Sourcing adheres strictly to authorized Shopify/WooCommerce API connections or validated CSV feed uploads.

---

## 3. Reconciled Contract Alignment

| Dimension | ADR-0001 Baseline | ADR-0005 Baseline | ADR-0009 Reconciled Standard |
| :--- | :--- | :--- | :--- |
| **Monetization Model** | Affiliate commissions | Direct brand partnerships | B2B2C Design Partner pilot fees + optional affiliate tracking |
| **Handoff Target** | Affiliate network redirect | Brand storefront | Direct brand storefront PDP with referral tracking |
| **Catalog Origin** | Sourced affiliate feeds | Direct authorized brand feeds | Authorized D2C brand catalogs (100–500 SKUs) |
| **Commerce Scope** | Frozen & unmounted | N/A | Strictly frozen per ADR-0001 (no cart, checkout, or payments) |

---

## 4. Consequences

- **Positive:** Resolves the architectural tension between affiliate redirection and direct brand onboarding without rewriting historical ADR-0001.
- **Positive:** Keeps the Pilot MVP engineering boundary strictly isolated from PCI-DSS, checkout flows, inventory race conditions, and returns logistics.
- **Governance:** Maintains continuity across all historical decision logs, audit trails, and product requirement documents.
