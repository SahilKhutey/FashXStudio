# Catalog Merchant Takedown Runbook

## 1. Statutory Context & 1-Hour SLA

When a brand partner, merchant, or copyright holder requests the removal of their catalog products (or terminates an affiliate agreement):
- **Target SLA**: Deactivation and feed exclusion within **60 minutes**.
- **Audit Requirement**: Document merchant request, authorized requester, reason, and time of completed removal.

---

## 2. Immediate Takedown Execution Steps

### Step 1: Deactivate Catalog Source (Admin API)
Deactivate the entire brand catalog source with a single command:
```bash
curl -X POST https://api.fashx.studio/api/v1/admin/sources/deactivate \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source_name": "flipkart_affiliate", "reason": "Merchant notice received on 2026-10-11"}'
```

### Step 2: Immediate SQL Fallback (Direct Database Intervention)
If the Admin API is degraded, execute via direct database session:
```sql
BEGIN;

-- 1. Deactivate source in catalog_sources
UPDATE catalog_sources 
SET is_active = FALSE, deactivated_at = NOW() 
WHERE name = 'TARGET_MERCHANT_NAME';

-- 2. Mark all garments from this merchant as unavailable/hidden
UPDATE canonical_garments 
SET is_active = FALSE 
WHERE source_id = (SELECT id FROM catalog_sources WHERE name = 'TARGET_MERCHANT_NAME');

-- 3. Deactivate active merchant offers
UPDATE merchant_offers 
SET in_stock = FALSE 
WHERE merchant_name = 'TARGET_MERCHANT_NAME';

COMMIT;
```

---

## 3. Feed & Cache Invalidation

1. **Evict Redis Cache**:
   - Clear cached feed pages and recommendations:
     ```bash
     redis-cli -u $REDIS_URL DEL "feed:*" "recommendations:*"
     ```
2. **Verify Feed Exclusion**:
   - Run verification query:
     ```sql
     SELECT count(*) 
     FROM canonical_garments g 
     JOIN catalog_sources s ON g.source_id = s.id 
     WHERE s.name = 'TARGET_MERCHANT_NAME' AND g.is_active = TRUE;
     -- MUST RETURN 0
     ```
3. **Notify Requester**:
   - Issue written confirmation to brand/merchant counsel confirming deactivation within the 1-hour window.
