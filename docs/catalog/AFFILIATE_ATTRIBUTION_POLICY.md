# Affiliate Attribution Policy

**Workstream**: 5.1.10 — Affiliate Links, Networks & Commission Attribution  
**Status**: Active  
**Enforcement Engine**: `backend/fashx/catalog/authorization/`

---

## 1. Scope
Affiliate attribution occurs when FashXStudio partners with an affiliate network (e.g., CJ, Rakuten, Impact, ShareASale, Amazon Associates) or direct merchant partner affiliate program to earn a commission on referred sales.

---

## 2. Policy Invariants

1. **Explicit Permission Required**:
   Affiliate tracking parameters or redirection wrappers may ONLY be applied if the source holds the `AFFILIATE_ATTRIBUTION` permission.
2. **Network Agreement Evidence**:
   Every source utilizing `AFFILIATE_ATTRIBUTION` must link to verified contractual evidence (`CatalogAuthorizationEvidence`) establishing the network relationship and publisher ID.
3. **Transparency & FTC / ASCI Compliance**:
   All commercial links that earn affiliate compensation must display clear disclosures to shoppers (e.g. "We may earn a commission when you buy through our links") in compliance with consumer protection standards.

---

## 3. Redirect Synthesis Pipeline

```
+-------------------------------------------------------+
|  Shopper Clicks "Buy at Zara"                         |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|  Check Authorization:                                 |
|  1. MERCHANT_REDIRECT      --> ALLOW                  |
|  2. AFFILIATE_ATTRIBUTION --> ALLOW                   |
+-------------------------------------------------------+
                           |
            +--------------+--------------+
            |                             |
      (Both ALLOWED)               (AFFILIATE DENIED)
            |                             |
            v                             v
+-----------------------+     +-----------------------+
| Generate Tracked Link |     | Direct PDP Deep-Link  |
| with Approved Token   |     | Clean URL without Ad  |
| & Network Parameters  |     | Redirect Wrapper      |
+-----------------------+     +-----------------------+
```

---

## 4. Verification Check
- Test coverage: `tests/catalog/test_permissions_and_evaluator.py::test_cat_perm_017_commercial_redirect_and_affiliate_attribution`.
