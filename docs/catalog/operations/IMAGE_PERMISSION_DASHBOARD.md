# Image Permission Status Dashboard

## 1. Architectural Invariant
In FashXStudio, product image rights follow strict operational boundaries:
> An image URL is not permission to download; permission to download is not permission to store; permission to display is not permission to process with AI; and permission to process is not automatically permission to create or retain a VTO derivative.

The image permission status dashboard (`GET /api/v1/merchant/sources/{id}/image-permissions`) evaluates these rights and surfaces real-time warnings to merchant operators.

---

## 2. Multi-Operation Permission Breakdown

```mermaid
graph TD
    Source[Catalog Source] --> CheckFetch{IMAGE_FETCH Granted?}
    CheckFetch -->|Yes| Fetch[Fetch Permitted]
    CheckFetch -->|No| NoFetch[Images Not Downloadable]

    Fetch --> CheckStore{IMAGE_STORE Granted?}
    CheckStore -->|Yes| Store[Mirror Storage Permitted]
    CheckStore -->|No| Hotlink[Hotlink Policy Only]

    Fetch --> CheckDisplay{IMAGE_DISPLAY Granted?}
    CheckDisplay -->|Yes| Display[Display Permitted on Shopper Catalog]
    CheckDisplay -->|No| WarnDisplay[Warning: Images Hidden from Shoppers]

    Fetch --> CheckAI{IMAGE_AI_PROCESS Granted?}
    CheckAI -->|Yes| AI[Segmentation & Extraction Permitted]
    CheckAI -->|No| WarnAI[Warning: AI Garment Parsing Disabled]

    AI --> CheckVTO{VTO_PROCESS Granted?}
    CheckVTO -->|Yes| VTO[Virtual Try-On Permitted]
    CheckVTO -->|No| WarnVTO[Warning: Virtual Try-On Disabled]

    Store & (Display | VTO) --> Deriv[Derivatives Retained]
```

---

## 3. Operations Matrix & Policy Verification

| Operation | Governing Permission Code | Policy Impact When Not Granted |
| :--- | :--- | :--- |
| **`fetch_permitted`** | `IMAGE_FETCH` | Pipeline will not download external image assets. |
| **`store_permitted`** | `IMAGE_STORE` | Raw original bytes cannot be stored in FashXStudio private S3 storage. |
| **`display_permitted`** | `IMAGE_DISPLAY` | Display thumbnails and detail derivatives cannot be rendered in mobile/web client. |
| **`ai_processing_permitted`**| `IMAGE_AI_PROCESS` | Garment segmentation ML models will skip assets from this source. |
| **`vto_permitted`** | `VTO_PROCESS` | Virtual try-on generation button is disabled for products from this source. |
| **`derivatives_retained`**| `DERIVATIVE_STORE` | Generated derivatives are purged immediately after session completion. |

---

## 4. Asset Inventory Reporting
The dashboard queries `catalog_image_assets` to report:
- `total_assets_count`: Total registered images from this source.
- `active_assets_count`: Currently active, validated images serving display or VTO.
- `suspended_assets_count`: Assets placed on hold due to licensing review or takedown requests.
- `warning_messages`: Actionable warnings identifying missing permissions.
