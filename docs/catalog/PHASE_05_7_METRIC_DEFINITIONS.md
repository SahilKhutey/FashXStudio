# Phase 05.7 — Catalog Metric Definitions

## 1. Scope
This specification provides rigorous mathematical definitions, operational boundary conditions, and inclusion/exclusion criteria for all 7 catalog target metrics.

---

## 2. Metric Specifications

### 2.1 CAT-TGT-01: Live Authorized Merchant Feeds
- **Definition:** The number of unique catalog sources that represent authentic, live retailer integrations passing full compliance verification.
- **Formula:**
  $$\text{CAT-TGT-01} = \sum_{s \in S} \mathbb{I}(\text{is\_live\_qualified}(s))$$
- **Qualification Criteria:**
  - `source_status` $\in \{\text{APPROVED}, \text{ACTIVE}, \text{AUTHORIZED}\}$
  - `is_enabled == True` and `operational_status == 'ENABLED'`
  - Expiration date is in the future or null (`expires_at > now` or `None`)
  - Backed by verified legal evidence (`authorization_reference` or verified record in `catalog_authorization_evidence`)
  - Associated `Merchant.verification_status` $\in \{\text{VERIFIED}, \text{ACTIVE}\}$
  - At least 1 successful sync run recorded in `ingest_runs` with status `ok` or `completed`
- **Disqualifications:**
  - Adapter names containing `mock`, `fixture`, `test_stub`, or `seed_file`
  - Source kinds matching `manual` or `file_drop_fixture`

---

### 2.2 CAT-TGT-02: Usable Catalog Products
- **Definition:** The total count of distinct, active, merchant offers eligible for shopper display.
- **Formula:**
  $$\text{CAT-TGT-02} = |\{o \in \text{MerchantOffers} : \text{passes\_all\_usability\_checks}(o)\}|$$
- **14 Mandatory Usability Checks:**
  1. Offer `status == 'ACTIVE'`
  2. Not a duplicate `(merchant_id, source_product_id)` pair
  3. Not present in `catalog_ingestion_quarantine` with status `PENDING`
  4. Parent source is authorized and enabled (`is_enabled == True`)
  5. Parent source is not expired, suspended, or revoked
  6. Merchant `verification_status` is `VERIFIED` or `ACTIVE`
  7. Non-null, strictly positive price (`price_minor > 0`)
  8. Valid destination URL starting with `http://` or `https://`
  9. Associated merchant product or canonical garment has a valid title ($\ge 3$ characters)
  10. Currency code populated (3-character ISO 4217)
  11. Offer availability is defined (e.g., `IN_STOCK`, `OUT_OF_STOCK`)
  12. Valid stock boolean flag
  13. Source synchronization record exists
  14. Offer not subject to active takedown request

---

### 2.3 CAT-TGT-03: Controlled Catalog Expansion
- **Definition:** Controlled verification gate evaluating whether catalog density is ready for scaling between 2,000 and 5,000 usable offers.
- **Rule:** Expansion to this volume is permitted only when baseline quality gates (freshness, link health, source compliance) are in `PASS` state.

---

### 2.4 CAT-TGT-04: Price Freshness
- **Definition:** The percentage of sampled active offers whose pricing was verified within the source's agreed freshness window.
- **Formula:**
  $$\text{CAT-TGT-04} = \frac{\sum_{o \in \text{Sample}} \mathbb{I}(\text{last\_price\_verified\_at} \ge \text{now} - T_{\text{freshness}}(s))}{|\text{Sample}|} \times 100\%$$
- **Default Window ($T_{\text{freshness}}$):** Defined per source via `CatalogSource.freshness_policy_hours` (default 24 hours).
- **Classification Rules:**
  - $\text{last\_price\_verified\_at} \ge \text{cutoff} \implies \text{FRESH}$
  - $\text{last\_price\_verified\_at} < \text{cutoff} \implies \text{STALE}$
  - $\text{last\_price\_verified\_at} \text{ is None} \implies \text{UNVERIFIED}$

---

### 2.5 CAT-TGT-05: Broken Product Link Rate
- **Definition:** The percentage of sampled active offers whose merchant destination links return client/server error codes or fail routing.
- **Formula:**
  $$\text{CAT-TGT-05} = \frac{|\{o \in \text{Sample} : \text{status}(o) \in \{\text{BROKEN}, \text{BROKEN\_OR\_REMOVED}, \text{INVALID\_REDIRECT}\}\}|}{|\text{Sample}|} \times 100\%$$
- **Classification Rules:**
  - HTTP 200–399 (excluding SSRF blocked redirects) $\implies \text{VALID}$
  - HTTP 404 $\implies \text{BROKEN}$
  - HTTP 410 $\implies \text{BROKEN\_OR\_REMOVED}$
  - HTTP 401, 403 $\implies \text{UNAVAILABLE}$
  - HTTP 429, 500, 502, 503, 504 (after retry) $\implies \text{TEMPORARY\_FAILURE}$
  - SSRF block / internal IP resolution / loopback redirect $\implies \text{INVALID\_REDIRECT}$

---

### 2.6 CAT-TGT-06: Zero Unauthorized Sources
- **Definition:** Count of operational or cleared catalog sources that lack active, verified legal authorization evidence.
- **Target Value:** Exactly $0$ ($100\%$ zero-tolerance compliance).
- **Formula:**
  $$\text{CAT-TGT-06} = \sum_{s \in S} \mathbb{I}((\text{is\_enabled}(s) \lor \text{cleared}(s)) \land \neg \text{is\_authorized}(s))$$

---

### 2.7 CAT-TGT-07: Image Permission Traceability
- **Definition:** The percentage of active image assets with verified lineage and documented operational permissions across all 6 image lifecycle operations.
- **Target Value:** Exactly $100.0\%$.
- **Required Lineage:**
  - Valid `merchant_id` and `source_id`
  - Valid `original_storage_key` or `source_reference`
  - Granular rights recorded for: Fetch, Store, Display, AI Processing, VTO, Derivative Generation.
