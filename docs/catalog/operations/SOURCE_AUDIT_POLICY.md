# Source Audit Policy

## 1. Compliance and Non-Repudiation
All operational modifications, manual triggers, configuration changes, takedowns, product overrides, and offer deactivations must leave an immutable audit trail in `catalog_source_audit_events`.

---

## 2. Audit Event Schema
- `id`: UUID primary key.
- `actor_id`: UUID of the user who performed the operation (or null for automated background jobs).
- `actor_role`: Role of the operator (`PLATFORM_ADMIN`, `MERCHANT_OPERATOR`, `SYSTEM`).
- `merchant_id`: Tenant identifier.
- `source_id`: Source identifier.
- `entity_type`: Target entity (`SOURCE`, `SCHEDULE`, `SYNC_RUN`, `PRODUCT_OVERRIDE`, `OFFER`, `TAKEDOWN`).
- `entity_id`: String ID of the affected record.
- `action`: Specific operational action (e.g. `SOURCE_CONNECTED`, `SOURCE_STATUS_CHANGED`, `SYNC_TRIGGERED`, `SCHEDULE_UPDATED`, `PRODUCT_OVERRIDE_SET`, `OFFER_DEACTIVATED`, `TAKEDOWN_REQUESTED`).
- `reason_code`: Standard reason or custom operator explanation.
- `safe_change_summary`: JSON payload detailing before/after changes with all sensitive credentials and tokens scrubbed.
- `request_id`: Tracing correlation identifier.
- `outcome`: `SUCCESS`, `DENIED`, or `FAILED`.
- `created_at`: UTC timestamp.

---

## 3. Tenant-Scoped Query Isolation
- Merchants querying `GET /api/v1/merchant/audit` receive only audit rows where `merchant_id == current_merchant_id`.
- Platform administrators querying audit trails can inspect cross-merchant events for compliance and security auditing.
- Audit records are append-only; update and delete operations are restricted by database permissions.
