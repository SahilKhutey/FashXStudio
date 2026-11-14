# FashXStudio — Business Model & Monetization Hypotheses

**Document ID:** `FASHX-BIZ-001`  
**Version:** `1.0 — Approved Baseline`  
**Date:** `10 November 2026`  
**Status:** `Approved Commercial Hypothesis`  
**Scope:** `Phase 01 — Commercial Strategy & Unit Economics Baseline`  

---

## 1. Commercial Proposition & Stakeholder Value

FashXStudio operates on a **B2B2C architecture with a B2B-first commercialization strategy**. The commercial platform is funded by fashion merchants and D2C brands who derive measurable value from increased customer engagement, visual confidence, and qualified purchase intent.

### Multi-Stakeholder Value Exchange
- **For Shoppers:** Free, personalized fashion discovery and high-fidelity virtual try-on on their own photos, eliminating the guesswork of online apparel shopping.
- **For Merchants:** A powerful new visual channel that transforms static product photography into high-converting virtual fitting rooms, driving qualified traffic directly to product detail pages.
- **For FashXStudio:** Predictable SaaS platform subscriptions and high-margin usage fees per completed try-on generation.

---

## 2. Revenue Model Hypotheses

| Commercial Model | Description | Initial Pilot Status | Long-Term Strategic Role |
| :--- | :--- | :--- | :--- |
| **Design Partner Pilot** | Waived or subsidized pilot fee in exchange for feed access and telemetry cooperation. | **Active Pilot Model** | Vehicle for initial technical and market validation. |
| **Merchant Monthly SaaS** | Fixed recurring subscription (₹15,000–₹35,000/month) covering catalog sync and dashboard. | **Hypothesis** | Core baseline revenue for mid-tier D2C brands. |
| **Usage-Based VTO Fees** | Metered fee per completed try-on (₹3.50–₹5.00) beyond included plan quotas. | **Hypothesis** | High-margin expansion revenue scaling with shopper engagement. |
| **Affiliate Commissions** | 2% to 8% commission on attributable purchases through authorized merchant networks. | **Secondary/Optional** | Incremental revenue channel where affiliate networks exist. |
| **Enterprise Licensing** | Custom white-label widget and dedicated SLA contracts for large apparel retailers. | **Post-Pilot (V2)** | Enterprise expansion path for scaled brand groups. |

---

## 3. Unit Economics Framework

### Contribution Margin per Try-On

$$\text{Contribution per VTO} = \text{Revenue per VTO} - C_{\text{VTO}}$$

Where direct variable cost is governed by:

$$C_{\text{VTO}} = C_{\text{provider}} + C_{\text{storage}} + C_{\text{compute}} + C_{\text{infrastructure}}$$

### Target Pilot Economics
- Planned billable rate per VTO unit: **₹35.00** (or bundled equivalent in monthly SaaS tier).
- Maximum direct cost ceiling ($C_{\text{VTO}}$): **₹11.50** (Provider API ₹8.50 + S3 ₹0.75 + Worker ₹1.50 + DB ₹0.75).
- **Target Contribution Margin:** $\ge 65\%$.

---

## 4. Eight Core Business Model Validation Questions

Before finalizing permanent subscription pricing and committing to enterprise sales cycles, the following eight commercial questions must be answered using real pilot evidence:

1. Does the D2C merchant observe an increase in outbound purchase intent from shoppers who use VTO?
2. Is the merchant willing to pay a pay-per-generation fee (₹3.50–₹5.00) for completed try-ons?
3. Does the merchant prefer a flat, predictable monthly SaaS tier over variable usage billing?
4. What monthly try-on volume is considered commercially meaningful by brand founders?
5. What is FashXStudio's actual, verified cost per try-on under live network conditions and retry rates?
6. Does the merchant require verified post-checkout conversion data to justify recurring payment?
7. Can the merchant legally and technically provide order conversion webhooks to FashXStudio?
8. What ongoing operational and customer support hours are required to maintain a connected brand feed?
