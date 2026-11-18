# Retailer Integration Assessment: Flipkart

## 1. Technical & Commercial Status

- **Adapter File:** `backend/fashx/catalog/acquisition/adapters/flipkart.py`
- **Classification:** `FIXTURE_ONLY` / `MOCK` (`IntegrationStatus.MOCK`)
- **Live Integration Viable:** No (Requires bilateral enterprise partner agreement)

## 2. API & Access Analysis

1. **Affiliate Program Terms**:
   - The Flipkart Affiliate API provides access to listing feeds and product prices for affiliate redirect purposes.
   - However, Flipkart’s affiliate agreement explicitly restricts:
     - Using data to power competing recommendation engines or multi-store comparison features without prior written approval.
     - Storing images or creating derivative works (including AI model fine-tuning and image transformations).
2. **Rate Limits and Data Freshness**:
   - Standard affiliate feed access enforces strict IP rate limiting and restricts real-time polling to predefined intervals.
3. **Current Code State**:
   - `FlipkartAdapter` is maintained as a fixture-based simulation (`IntegrationStatus.MOCK`).
   - It cannot be activated for live crawling without verified bilateral authorization and image processing licensing.
