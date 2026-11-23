# Catalog Authorization Engine Specification

**Workstream**: 5.1.14 — 11-Step Fail-Closed Decision Engine  
**Status**: Active  
**Module**: `backend/fashx/catalog/authorization/evaluator.py`

---

## 1. Architectural Philosophy
The Catalog Authorization Engine is the centralized decision core for all catalog operations in FashXStudio. It implements a **zero-trust, fail-closed policy evaluation algorithm**. 

No product data is stored, indexed, served, or processed through AI models unless the authorization engine explicitly evaluates all 11 policy gates and issues an `ALLOW` verdict with reason code `PERMITTED_BY_POLICY`.

---

## 2. 11-Step Fail-Closed Decision Flow

```
                      [ Incoming Request ]
                               |
                               v
                     [ 1. Source Exists? ] -------> NO ----> DENY_SOURCE_NOT_FOUND
                               | YES
                               v
                  [ 2. Merchant Verified? ] ------> NO ----> DENY_MERCHANT_NOT_VERIFIED
                               | YES
                               v
                   [ 3. Source Status ACTIVE? ] ---> NO ----> DENY_SOURCE_NOT_ACTIVE / SUSPENDED
                               | YES
                               v
                  [ 4. No Active Takedown? ] -----> NO ----> DENY_SOURCE_TAKEDOWN_ACTIVE
                               | YES
                               v
                  [ 5. Verified Evidence? ] ------> NO ----> DENY_NO_VERIFIED_EVIDENCE
                               | YES
                               v
                 [ 6. Explicit Perm Granted? ] ---> NO ----> DENY_PERMISSION_NOT_FOUND
                               | YES
                               v
                  [ 7. Perm Not Revoked? ] -------> NO ----> DENY_PERMISSION_REVOKED
                               | YES
                               v
                  [ 8. Perm Time Valid? ] --------> NO ----> DENY_PERMISSION_NOT_YET_EFFECTIVE / EXPIRED
                               | YES
                               v
                  [ 9. Category In-Scope? ] ------> NO ----> DENY_CATEGORY_OUT_OF_SCOPE
                               | YES
                               v
                 [ 10. Market In-Scope? ] --------> NO ----> DENY_MARKET_OUT_OF_SCOPE
                               | YES
                               v
                 [ 11. Processor Permitted? ] ----> NO ----> DENY_PROCESSOR_NOT_PERMITTED
                               | YES
                               v
                   ===>>> [ ALLOW ] <<<===
                   PERMITTED_BY_POLICY (Logged with correlation ID)
```

---

## 3. Reason Code Dictionary

| Reason Code | Decision | Meaning |
|---|---|---|
| `DENY_SOURCE_NOT_FOUND` | DENY | Source ID is unknown to the registry |
| `DENY_MERCHANT_NOT_VERIFIED` | DENY | Parent merchant is UNVERIFIED, UNDER_REVIEW, REJECTED, or SUSPENDED |
| `DENY_SOURCE_SUSPENDED` | DENY | Source is currently in SUSPENDED status |
| `DENY_SOURCE_EXPIRED` | DENY | Source has reached or passed its contractual expiration timestamp |
| `DENY_SOURCE_NOT_ACTIVE` | DENY | Source is in PENDING_REVIEW, APPROVED, or REJECTED status |
| `DENY_SOURCE_TAKEDOWN_ACTIVE` | DENY | An active takedown notice is currently open against this source |
| `DENY_NO_VERIFIED_EVIDENCE` | DENY | No verified legal contract or authorization document is on record |
| `DENY_PERMISSION_NOT_FOUND` | DENY | Requested granular operation code is not registered for this source |
| `DENY_PERMISSION_NOT_GRANTED` | DENY | Permission record exists but status != GRANTED |
| `DENY_PERMISSION_REVOKED` | DENY | Permission has been explicitly revoked (`revoked_at` is set) |
| `DENY_PERMISSION_NOT_YET_EFFECTIVE` | DENY | Current timestamp is before permission `effective_at` |
| `DENY_PERMISSION_EXPIRED` | DENY | Current timestamp is after permission `expires_at` |
| `DENY_CATEGORY_OUT_OF_SCOPE` | DENY | Product category is outside permitted `scope_categories` |
| `DENY_MARKET_OUT_OF_SCOPE` | DENY | Target market country is outside permitted `scope_markets` |
| `DENY_PROCESSOR_NOT_PERMITTED` | DENY | Requested AI processor is not in `processor_restrictions` |
| `PERMITTED_BY_POLICY` | ALLOW | All 11 gates passed; operation authorized |

---

## 4. Audit Logging Invariant
Every call to `CatalogAuthorizationService.evaluate` results in an immutable row inserted into `catalog_authorization_decisions`. The record contains:
- `source_id`, `product_id`, `operation`, `decision`, `reason_code`, `permission_id`, `processor_id`, `market`, `category`, `correlation_id`, `evaluated_at`.
- Enables end-to-end tracing of all allowed and denied operations for regulatory and partner audits.
