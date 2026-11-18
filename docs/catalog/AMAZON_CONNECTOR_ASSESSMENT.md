# Retailer Integration Assessment: Amazon

## 1. Technical & Commercial Status

- **Adapter File:** `backend/fashx/catalog/acquisition/adapters/amazon.py`
- **Classification:** `FIXTURE_ONLY` / `MOCK` (`IntegrationStatus.MOCK`)
- **Live Integration Viable:** No (Requires bilateral agreement / Creators API access)

## 2. API & Access Analysis

1. **PA-API 5.0 Deprecation / Restructuring**:
   - Amazon has transitioned standard affiliate access away from classical PA-API 5.0 bulk extraction toward the Amazon Creators API and Associates Central tools.
   - Traditional PA-API access requires active sales generation (at least 3 qualifying sales every 30 days) or account credentials become throttled/deactivated.
2. **Derivative Works & Image Usage Rights**:
   - The Amazon Associates Operating Agreement explicitly restricts caching of product images beyond 24 hours.
   - Using Amazon product images as inputs to AI pipelines (including computer vision segmentation, garment warping, and virtual try-on) is strictly prohibited without explicit bilateral licensing from Amazon and respective brand rights holders.
3. **Current Code State**:
   - `AmazonAdapter` in FashXStudio operates exclusively against mock fixture data.
   - It is classified as `IntegrationStatus.MOCK`.
   - It will not be registered as an `ACTIVE` source in production until written bilateral licensing is executed.
