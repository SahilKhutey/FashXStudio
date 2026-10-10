# ADR-0005: Catalog Sourcing, Provenance, and Rights Management

- **Status:** Accepted
- **Date:** 2026-10-10
- **Owner:** Sahil Khutey

---

## 1. Context

Virtual try-on requires high-resolution garment pixels processed server-side to generate synthesized on-model imagery. Most commercial affiliate networks (Cuelinks, EarnKaro, Impact) and retail platform terms (Amazon Associates, Flipkart Affiliate ToU) restrict image modifications, derivative works, or competitive comparison platforms. Scraping product websites without authorization violates platform terms and intellectual property rights.

To build a legally compliant, high-quality catalog in India, FashXStudio must source catalog items solely from channels where explicit, verifiable permission has been granted for:
1. Product metadata display and affiliate link-out.
2. Direct image display in consumer applications.
3. Server-side AI processing (visual attribute extraction and virtual try-on generation).

---

## 2. Options Considered

### Option A: Scraping Indian E-Commerce Portals
- **Pros:** Fast access to large catalogs.
- **Cons:** Strictly prohibited by Rule I08 and copyright law; fragile HTML parsing; immediate risk of IP litigation and C&D notices; violates core architectural integrity.
- **Decision:** **Strictly Rejected.**

### Option B: Major Affiliate APIs (Amazon PA-API, Flipkart API, Affiliate Networks)
- **Amazon:** PA-API 5.0 is deprecated; the replacement Creators API requires an active Associates account with ≥10 qualifying sales in 30 days. Link-out deep links are supported, but raw product feeds are unavailable.
- **Flipkart Affiliate API:** Provides product and delta feeds with a 20 rps limit. However, the Terms of Use prohibit derivative works and deployment on competitive platforms. AI try-on could be interpreted as a derivative work. Requires written legal clarification before production ingestion.
- **Affiliate Networks (Cuelinks, Admitad):** Cuelinks provides transaction and link generation APIs only (no merchant feeds). Admitad advertisers supply Google Merchant feeds, but publisher access requires per-program approval.
- **Decision:** Supplemental / challenger sources pending formal written clarification.

### Option C: Direct Brand Partnerships (Indian D2C Fashion Brands) — Selected Strategy
- **Pros:** Clear written agreements covering display rights, AI try-on derivation rights, image mirroring in object storage, and verified takedown contacts. Clean feed formats (Google Merchant CSV/XML or Shopify exports).
- **Cons:** Requires active partner outreach and business development lead time.
- **Decision:** **Adopted as primary strategy.** Pilot launch targets 3-5 direct brand partners (e.g. FabIndia, Snitch, Westside) with verified written agreements.

---

## 3. Core Architectural Rules

1. **No Scraping:** Zero automated web scraping under any circumstance.
2. **Written Clearance Prerequisite:** No source can enter `status='cleared'` without an immutable evidence link to a written agreement (`clear_source.py --evidence-url ...`).
3. **Try-On Requires Mirroring:** A source with `rights_tryon = true` must have `image_policy = 'mirror'` (`ck_tryon_requires_mirror`). Hotlink-only sources cannot participate in virtual try-on.
4. **Instant Kill-Switch (Purge / Takedown):** Any source can be suspended or completely purged (database rows, embeddings, and object storage assets) via CLI in ≤ 10 minutes.
5. **Default Feed Filtering:** Discovery feed stage 1 strictly filters `catalog_sources.status = 'cleared'` AND `products.status = 'active'`. Synthetic seed demo data remains `status='suspended'` (tests only).

---

## 4. Pre-Registered Acceptance Thresholds (Committed Prior to Ingestion & Scoring)

| Metric | Threshold |
|---|---|
| **Category Accuracy** | ≥ 95.0% |
| **Sub-Category Accuracy** | ≥ 90.0% |
| **Primary Color Family** | ≥ 90.0% |
| **Visual Attributes (Pattern, Sleeve, Neckline, Length)** | ≥ 85.0% each |
| **Ethnic-Wear Classification Flag** | ≥ 95.0% |
| **`tryon_suitable` Precision** | ≥ 90.0% |
| **Dedup False-Merge Rate** | ≤ 1.0% |
| **Embedding Neighbor Purity (Top-10 Sub-Category)** | ≥ 0.80 |
| **Price Freshness (Price Checked ≤ 72h)** | ≥ 95.0% of active products |
| **Unmapped-Category Products** | ≤ 3.0% of total feed |
| **Takedown SLA Execution** | ≤ 10 minutes |

---

## 5. Decision and Consequences

- We adopt **Direct Brand Partnerships** as the foundation of the FashX catalog, supplemented by cleared affiliate feeds once written terms are verified.
- The schema will track `catalog_sources`, `ingest_runs`, `category_map`, and enrich `merchant_products` with provenance and freshness columns (`source_id`, `source_product_id`, `item_group_id`, `content_hash`, `status`, `last_seen_at`, `price_checked_at`).
- All product records must represent prices in INR.
