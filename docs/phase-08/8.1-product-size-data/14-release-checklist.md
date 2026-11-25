# 14 — Release Readiness Checklist

## 1. Readiness Verification Matrix

| Checklist Item | Target Status | Verification Mechanism |
|---|---|---|
| Alembic Migration `0056` | Verified | Migration file created and validated |
| Database Models Exported | Complete | `database/models/__init__.py` updated with all 9 models |
| Unit Normalization Precision | Verified | Unit tests pass with `Decimal` Round Half-Up |
| Sizing System Conversion Guard | Verified | Tests confirm refusal of unverified conversions |
| Fail-Closed API Contract | Verified | Returns explicit `UNAVAILABLE` payload on missing chart |
| Separation from Fit Prediction | Enforced | Mandatory disclaimers present in schemas and UI |
| Mobile Components Implemented | Complete | `mobile/src/features/product-size/` created and exported |
| Multi-tenant Isolation | Enforced | Product and merchant ownership verified on ingestion |
| Quarantine Workflow | Active | Invalid payloads stored in `size_chart_quarantine` |
| Automated Test Suite | Passing | Comprehensive test runner validates all test cases |

## 2. Operational Runbook

### 2.1 Ingestion Pipeline Health
- Monitor `size_chart_quarantine` counts by `merchant_id`. An increase in quarantined charts signals a merchant feed schema change.
- Monitor `size_chart_events` for `VERSION_INCREMENTED` vs `NO_OP_UNCHANGED` ratios.

### 2.2 Inventory Freshness Degradation
- Inventory snapshots older than 24 hours degrade automatically to `UNKNOWN`. Alert if merchant inventory feeds fail to update for $> 12$ hours.
