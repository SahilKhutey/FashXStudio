# Source Takedown Runbook

**Workstream**: 5.1.13 — Source Takedown & Emergency Suspension Procedures  
**Status**: Active  
**Enforcement Engine**: `backend/fashx/catalog/takedowns/`  
**SLA**: P0 Emergency Takedown < 15 minutes; Standard Takedown < 4 hours.

---

## 1. Takedown Triggers and Reason Codes

| Reason Code | Trigger Scenario | Initial Action |
|---|---|---|
| `IMAGE_RIGHTS_DISPUTE` | Copyright claim from photographer, model agency, or licensor | Immediate suspension of source images |
| `MERCHANT_REQUEST` | Merchant requests immediate removal of catalog | Immediate source suspension |
| `LICENSE_EXPIRED` | Licensing term concluded without renewal | Automated / manual suspension |
| `LICENSE_REVOKED` | Breach notice received from merchant counsel | Immediate source suspension |
| `DATA_RIGHTS_DISPUTE` | Dispute regarding pricing, descriptions, or trademarks | Immediate source suspension |
| `PROVIDER_TERMINATION` | Integration vendor / affiliate provider terminates service | Source suspension |
| `CREDENTIAL_COMPROMISE`| Stolen API keys, leaked tokens, or security alert | Immediate credential revocation & suspension |
| `SECURITY_INCIDENT` | Malicious payload, SSRF attempt, or corrupted feed | Immediate firewall block & suspension |
| `INCORRECT_PRODUCT_DATA`| Mass pricing error or misleading product listings | Immediate feed unpublishing |
| `LEGAL_REQUEST` | Court order, regulator notice, or law enforcement request | Immediate legal compliance suspension |

---

## 2. Emergency Suspension Protocol

```
+-------------------------------------------------------+
|  Takedown Notice Received                             |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|  POST /api/v1/admin/catalog/sources/{id}/takedown     |
+-------------------------------------------------------+
                           |
                           +-------------------------------------+
                           |                                     |
                           v                                     v
+--------------------------------------+  +--------------------------------------+
| 1. Synchronous Source Suspension     |  | 2. Create Audit Record               |
| - source_status = SUSPENDED          |  | - Insert catalog_takedown_requests   |
| - status = suspended                 |  | - Status = SUSPENDED                 |
| - rights_display = False             |  | - Record reason_code & requester     |
| - rights_tryon = False               |  +--------------------------------------+
+--------------------------------------+
                           |
                           v
+-------------------------------------------------------+
| 3. Authorization Engine Immediate Lockout            |
| - All operations for source_id return DENY            |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
| 4. Async Worker Unpublishing (TakedownAsyncWorker)   |
| - MerchantProduct status = "suspended"                |
| - Flush Redis Edge CDN cache                          |
| - Cancel queued Celery try-on and inference jobs      |
+-------------------------------------------------------+
```

---

## 3. Resolution and Reinstatement Workflow
1. **Triaging**:
   - Senior catalog reviewer assigned via `POST /api/v1/admin/catalog/takedowns/{id}/triage`.
   - Reviewer audits root cause and communicates with merchant contacts.
2. **Resolution**:
   - Requisite cure executed (e.g., license renewed, disputed imagery purged, credentials rotated).
   - Takedown resolved via `resolve_takedown` with detailed resolution notes.
3. **Reinstatement Approval**:
   - Source is NOT automatically resumed upon takedown resolution.
   - An explicit administrative action `POST /api/v1/admin/catalog/sources/{id}/resume` is required.
   - The authorization engine validates that active evidence and granted permissions exist before allowing transition back to `ACTIVE`.
