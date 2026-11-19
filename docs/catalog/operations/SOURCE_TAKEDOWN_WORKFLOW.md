# Source Takedown Workflow

## 1. Overview and Operational Urgency
When a retailer partnership ends, licensing agreements expire, or a legal takedown notice is served, platform administrators must be able to immediately and atomically suspend a catalog source, cancel active jobs, deactivate public offers, and purge/suspend stored image assets.

---

## 2. Emergency Takedown Execution Flow

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Platform Administrator
    participant API as Admin Operations Router (/api/v1/admin/sources/{id}/takedown)
    participant Svc as SourceTakedownService
    participant DB as Postgres Database
    participant Storage as Object Storage (S3)

    Admin->>API: POST /admin/sources/{id}/takedown
    Note over Admin,API: Payload: reason_code, reason_text, purge_images: true
    API->>Svc: execute_takedown(source_id, payload)
    
    rect rgb(240, 220, 220)
        Note over Svc,DB: Atomic Takedown Transaction
        Svc->>DB: Set CatalogSource source_status=SUSPENDED, is_enabled=False
        Svc->>DB: Set CatalogSourceSchedule enabled=False
        Svc->>DB: Abort all running & queued IngestRuns
        Svc->>DB: Update all MerchantOffers to status=SUSPENDED, in_stock=False
        alt purge_images == true
            Svc->>DB: Mark all CatalogImageAssets as SUSPENDED
        end
        Svc->>DB: Record immutable TAKEDOWN_REQUESTED audit event
    end

    DB-->>Svc: Transaction Committed
    Svc-->>API: SourceTakedownResponse
    API-->>Admin: 200 OK (Summary: cancelled jobs, deactivated offers, suspended assets)
```

---

## 3. Cascading Effects
1. **Source State**:
   - `source_status = "SUSPENDED"`
   - `operational_status = "SUSPENDED"`
   - `is_enabled = False`
2. **Job Abort**:
   - Active `IngestRun` rows set to `status = "aborted"` with message noting the takedown reason code.
3. **Offer Inactivation**:
   - Every `MerchantOffer` linked to `source_id` is marked `status = "SUSPENDED"` and `in_stock = False`.
   - Offers are immediately removed from search indexes and shopper feeds.
4. **Image Asset Safeguard**:
   - If `purge_images: true`, all `CatalogImageAsset` records linked to `source_id` transition to `status = "SUSPENDED"`, preventing display CDN delivery and try-on synthesis.
5. **Canonical Garment Retention**:
   - Any canonical garment associated with the deactivated offers is evaluated: if other authorized merchants still sell that garment, the canonical garment remains active; otherwise it is marked inactive.
