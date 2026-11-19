# Catalog Freshness Policy

## 1. Timestamp Semantics
- `first_ingested_at`: UTC timestamp of first accepted ingestion.
- `last_ingested_at`: Most recent accepted ingestion run.
- `last_changed_at`: Most recent meaningful attribute/price/stock change (not updated on routine polling).
- `last_seen_at`: Present in a successful source response.
- `last_verified_at`: Passed explicit field-level or entity verification.
- `last_price_verified_at`: Price explicitly validated from source.
- `last_availability_verified_at`: Stock level explicitly validated.

## 2. Default Freshness Targets
- Price: 6 hours
- Availability: 2 hours
- Title and Category: 24 hours
- Size Availability: 2 hours
- Product Image Reference: 7 days
- Merchant and Source Status: 15 minutes

## 3. Freshness State Machine
- `CURRENT`: Verified within target threshold.
- `STALE`: Age exceeds policy max age.
- `UNKNOWN`: No verification timestamp recorded.
- `REVIEW_REQUIRED`: Timestamp in future or anomaly detected.
