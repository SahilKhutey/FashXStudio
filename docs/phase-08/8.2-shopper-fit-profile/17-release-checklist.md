# 17 — Release Readiness Checklist

| Item | Status | Notes |
|---|---|---|
| Measurement definitions & explanations | Implemented | 12 fields in `measurement_definitions.py` |
| Category measurement policies (`FIT_POLICY_VERSION = 1.0`) | Implemented | 8 supported categories; unsupported fail closed |
| Unit normalization (`CM` / `KG`, `Decimal` `ROUND_HALF_UP`) | Implemented | Original unit + value preserved |
| Validation bounds & confirmation workflow | Implemented | `NEEDS_CONFIRMATION` for unusual values |
| Per-measurement timestamps & optimistic history | Implemented | `measured_at` separated from `created_at`/`updated_at` |
| Subjective fit & category preferences | Implemented | Separate from physical measurements & merchant charts |
| Cross-brand size equivalence prohibition | Implemented | `BrandSizeMappingError` / `INSUFFICIENT_DATA` |
| Purpose-specific consent & account erasure | Implemented | Integrated with `ConsentRecord` & `erase_account` |
| Zero-PII logging verified | Tested | Verified via `caplog` and audit inspection |
| Alembic `0057` live Postgres verification | Pending CI | Local Windows has no Postgres daemon (Rule 14) |
| Staging synthetic end-to-end verification | Pending Staging | Outside local development environment |
