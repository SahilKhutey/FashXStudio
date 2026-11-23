# Phase 05.7 — Initial Catalog Targets Specification

## 1. Executive Summary and Purpose
This document establishes the measurable, evidence-backed catalog targets for the first controlled FashXStudio pilot. These targets define what the catalog acquisition and ingestion systems must achieve before the catalog is qualified for real shoppers.

These targets are not claims about the current repository state or claims of completed third-party merchant partnerships. Instead, they specify the operational measurement framework, verifiable evaluation procedures, and release gate decision criteria required for Phase 05.7.

---

## 2. Core Target Matrix

| Target ID | Name | Objective & Scope | Target Value | Hard Blocker Gate? |
|:---|:---|:---|:---|:---|
| **CAT-TGT-01** | Live Authorized Merchant Feed | At least 1 live authorized merchant feed connected, synchronized, and verified against legal evidence. | $\ge 1$ live feed | Yes (Acceptance Gate) |
| **CAT-TGT-02** | Usable Catalog Products | Distinct active non-quarantined merchant offers passing all 14 mandatory usability rules. | $\ge 1,000$ usable offers | Yes (Acceptance Gate) |
| **CAT-TGT-03** | Controlled Catalog Expansion | Expansion band for post-pilot staging, conditioned on baseline quality gates. | 2,000–5,000 usable offers | Conditional Gate |
| **CAT-TGT-04** | Price Freshness | Sampled active offers verified against source freshness window policy ($\le 24\text{h}$ default). | $\ge 95.0\%$ fresh | Yes (Quality Gate) |
| **CAT-TGT-05** | Broken Product Link Rate | Sampled active offer destination links checked with SSRF protection; 4xx/dead links strictly below threshold. | $< 1.0\%$ broken links | Yes (Quality Gate) |
| **CAT-TGT-06** | Zero Unauthorized Sources | Absolute compliance check: zero active or enabled sources without verified authorization evidence. | $0$ unauthorized sources | Yes (Zero-Tolerance Gate) |
| **CAT-TGT-07** | Image Permission Traceability | Active image assets must trace 100% of permissions (fetch, store, display, AI, VTO, derivatives). | $100.0\%$ traceable | Yes (Zero-Tolerance Gate) |

---

## 3. Entity Separation & Count Integrity
To prevent misleading catalog metrics, FashXStudio explicitly distinguishes between three tiers of catalog entities:
1. **Canonical Garments (`canonical_garments`):** Brand-agnostic or merchant-unified garment concepts representing a single apparel item design.
2. **Merchant Offers (`merchant_offers`):** Specific merchant listings of a canonical garment with price, availability, currency, and destination checkout URL. If two merchants sell the same shirt, this constitutes $1$ canonical garment and $2$ distinct merchant offers.
3. **Product Variants (`product_variants`):** Distinct purchasable SKU variants (e.g. Size M in Olive Green).

All evaluations report these counts distinctly. A raw count of feed rows or variants must never be substituted for usable offers or garments.

---

## 4. Release Decision Logic
The evaluation engine executes an automated multi-gate decision algorithm:
- **`ACCEPT`**: All 7 baseline targets pass ($100\%$ compliance, $0$ unauthorized sources, $\ge 1$ live feed, $\ge 1,000$ usable offers, $\ge 95\%$ fresh prices, $< 1\%$ broken links).
- **`HOLD`**: Any single blocker fails. The evaluation report persists an immutable audit snapshot with the exact blocker explanations and disqualification details.
