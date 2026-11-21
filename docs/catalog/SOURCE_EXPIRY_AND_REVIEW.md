# Source Expiry and Review Schedule Specification

**Workstream**: 5.1.12 — Periodic Audits, Expiry Schedules & Renewal  
**Status**: Active  
**Worker**: `backend/fashx/catalog/authorization/expiry_worker.py`

---

## 1. Objective
Merchant agreements, licensing terms, and technical credentials are rarely permanent. FashXStudio enforces periodic automated review and automated expiry sweeps to ensure that expired sources and permissions are immediately halted from publishing data or processing images.

---

## 2. Review Timelines & Cadences

| Level | Cadence | Trigger | Action Required |
|---|---|---|---|
| Tier 1 Enterprise Brands | 12 Months | `next_review_at` | Legal contract renewal & security review |
| Tier 2 Regional Merchants | 6 Months | `next_review_at` | Verification of business status & catalog accuracy |
| Affiliate Networks | 3 Months | `next_review_at` | Affiliate agreement confirmation & URL check |
| API Tokens / Credentials | 90 Days | `expires_at` | Automated token rotation & secret check |

---

## 3. Automated Expiry Sweeps (`CatalogExpiryWorker`)

A scheduled background job executes every hour to evaluate expiry thresholds:

```python
# Pseudo-logic of CatalogExpiryWorker.scan_and_expire
1. Find all active CatalogSource records where expires_at is not null and expires_at < now():
   - Transition source_status -> EXPIRED
   - Set status -> suspended
   - Revoke rights_display -> False
   - Revoke rights_tryon -> False

2. Find all granted CatalogSourcePermission records where expires_at is not null and expires_at < now():
   - Transition permission_status -> EXPIRED
```

---

## 4. Advance Warning Alerts
- **T-30 Days**: Automated Slack notification to Partner Success and Catalog Operations.
- **T-14 Days**: Formal email notice to merchant Primary and Technical contacts requesting renewal documents.
- **T-7 Days**: Escalation notice warning of upcoming automated catalog suspension.
- **T-0 Days**: Hard expiration executed. Catalog source moved to `EXPIRED`. Products unpublished.
