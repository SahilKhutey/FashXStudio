# Merchant Product Removal Policy

## 1. Multi-Merchant Marketplace Invariant
FashXStudio operates a multi-merchant catalog where multiple retailers may offer the same canonical garment (e.g. a specific Levi's jacket or Nike sneaker).

> **Core Architectural Rule**:
> Deactivating or removing a merchant's offer must never delete or deactivate the underlying canonical garment if other authorized merchants continue to offer it.

---

## 2. Deactivation Mechanics

```mermaid
flowchart TD
    Req([POST /api/v1/merchant/offers/{id}/deactivate]) --> ValAuth{Offer belongs to Merchant?}
    ValAuth -- No --> Err403[Reject: Tenant Isolation Violation]
    ValAuth -- Yes --> DeactOffer[Set offer.status='INACTIVE', in_stock=false]
    DeactOffer --> CheckOther{Do other merchants have ACTIVE offers for garment_id?}
    CheckOther -- Yes --> KeepGarmentActive[Preserve canonical_garment.active = true]
    CheckOther -- No --> DisableGarment[Set canonical_garment.active = false, in_stock = false]
    KeepGarmentActive & DisableGarment --> AuditLog[Emit OFFER_DEACTIVATED Audit Event]
    AuditLog --> Ret([Return Deactivate Response])
```

---

## 3. Database State Changes
1. **`merchant_offers`**:
   - `status`: `"INACTIVE"`
   - `in_stock`: `False`
   - `updated_at`: `current_timestamp`
2. **`merchant_products`**:
   - Associated record marked `status = "inactive"`, `availability = "OUT_OF_STOCK"`.
3. **`canonical_garments`**:
   - Evaluated via SQL count:
     ```sql
     SELECT COUNT(*) FROM merchant_offers 
     WHERE garment_id = :garment_id 
       AND id != :offer_id 
       AND status = 'ACTIVE' 
       AND in_stock = true;
     ```
   - If `count > 0`: `canonical_garment.active` remains `True`.
   - If `count == 0`: `canonical_garment.active` transitions to `False` and `in_stock = False`.
4. **Audit Trail**:
   - Event `OFFER_DEACTIVATED` logged with `other_active_offers_remaining` count and `canonical_garment_retained` boolean.
