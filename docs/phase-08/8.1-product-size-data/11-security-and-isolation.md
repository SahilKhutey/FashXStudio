# 11 — Security and Isolation

## 1. Multi-Tenant Cross-Merchant Isolation

Size chart data is strictly isolated per merchant:
- Ingestion endpoints require merchant authentication and verify that `merchant_id` matches the product owner.
- Cross-merchant size chart reuse is prohibited: even if two merchants sell identical canonical garments, each merchant's size chart is ingested, verified, and revisioned independently.
- Size charts are never merged across merchants.

## 2. Protection of Private Shopper Data

In accordance with Phase 04 and Phase 07 privacy guarantees:
- Size charts and variant availability are public catalog data and contain zero personally identifiable shopper information (PII).
- Size chart ingestion logs and audit events track merchant IDs and source feeds, not shopper identities.
- Shopper measurement profiles (Phase 08.2+) are kept strictly separated in authenticated shopper domains.

## 3. Input Sanitization & Threat Mitigation

- Size labels are strictly sanitized (trimmed, max 64 characters, control characters stripped).
- Numeric values are checked for overflow, negative values, and NaN / infinity.
- Raw payloads stored in `size_chart_quarantine` are constrained to valid JSON and scoped to the submitting merchant.
