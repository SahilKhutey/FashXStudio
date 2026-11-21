# Retailer Integration Assessment: Myntra

## 1. Technical & Commercial Status

- **Adapter File:** `backend/fashx/catalog/acquisition/adapters/myntra.py`
- **Classification:** `FIXTURE_ONLY` / `MOCK` (`IntegrationStatus.MOCK`)
- **Live Integration Viable:** No (Requires bilateral enterprise partner agreement)

## 2. API & Access Analysis

1. **Developer Portal & Access Scope**:
   - The Myntra Developer Portal exposes APIs primarily for **Seller Listing Management**, warehouse inventory dispatch, and order fulfillment (for marketplace sellers).
   - Myntra does not provide a general public catalog extraction or open developer affiliate API for third-party consumer discovery platforms.
2. **Scraping & Terms of Use**:
   - Myntra’s terms of service strictly forbid automated data extraction, screen scraping, or reverse engineering of their mobile/web endpoints.
   - Any attempt to extract catalog feeds without a partnership agreement violates platform terms and intellectual property rights.
3. **Current Code State**:
   - `MyntraAdapter` in FashXStudio is a synthetic mock adapter simulating Indian apparel product formats (Kurtas, Sarees, Western wear).
   - It is explicitly marked `IntegrationStatus.MOCK` and flagged `FIXTURE_ONLY`.
   - Live activation is blocked until a formal bilateral B2B data sharing agreement is signed with Myntra Designs Pvt. Ltd.
