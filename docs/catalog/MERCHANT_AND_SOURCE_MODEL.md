# Merchant and Source Model Specification

## 1. Merchant Identity vs. Source Adapter
- **Merchant**: Represents legal and business commercial identity (`legal_name`, `country_code`, `verification_status`, `operational_status`).
- **Catalog Source**: Represents an authorized technical ingestion endpoint (`source_type`, `access_method`, `credential_secret_ref`, `source_status`).
- One merchant can maintain multiple catalog sources (e.g. API connector, partner export CSV, SFTP feed).

## 2. Operational vs. Verification Status
- **Merchant Verification Status**:
  - `UNVERIFIED`
  - `UNDER_REVIEW`
  - `VERIFIED`
  - `REJECTED`
  - `SUSPENDED`
- **Merchant Operational Status**:
  - `PENDING`
  - `ACTIVE`
  - `SUSPENDED`
  - `TERMINATED`

Suspending or terminating a merchant preserves all historical audit trails and price history.
