# Blueprint for First Live Merchant Integration

## 1. Candidate Evaluation & Strategy

Rather than attempting to reverse-engineer or scrape closed multi-brand marketplace platforms (Amazon, Myntra, Flipkart), FashXStudio's first live integration strategy focuses on:
1. **Direct D2C Fashion Brand Partners** (e.g. Shopify-based Indian D2C brands, custom WooCommerce merchants, or enterprise fashion retailers using headless APIs).
2. **Standardized Feed Integration** using `AuthorizedHttpFeedAdapter` with signed bilateral data-sharing contracts.

## 2. Onboarding Workflow

To transition a merchant from contact to live catalog ingestion:
```
[Merchant Onboarding Checklist]
               │
               ▼
   [Merchant Registration]
   - Legal name, registration number, country code, contact
               │
               ▼
   [Identity Verification]
   - MCA / GSTIN registration validation by FashX reviewer
               │
               ▼
   [Source Registration]
   - Feed URL, access method (HTTPS_FEED), market codes, category scopes
               │
               ▼
   [Bilateral Evidence Attachment]
   - Signed licensing contract uploaded to S3 with SHA256 verification
               │
               ▼
   [Granular Permission Grant]
   - PRODUCT_DATA_READ
   - PRODUCT_DATA_STORE
   - IMAGE_DISPLAY
   - (Optional) IMAGE_AI_PROCESS & VTO_PROCESS if contractually granted
               │
               ▼
   [Source Status: APPROVED -> ACTIVE]
               │
               ▼
   [Automated Sync Schedule (Full / Incremental)]
```

## 3. Deployment Checklist

- [ ] Merchant business identity verified in registry.
- [ ] Feed URL validated against host allowlist and SSRF policy.
- [ ] ETag and conditional request caching confirmed.
- [ ] Safe stale offer reconciliation verified on dry-run.
- [ ] Admin health check endpoint reports `HEALTHY`.
