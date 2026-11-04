# RC-06 — Catalog Acquisition & Discovery

## Ingestion to Consumer Presentation Pipeline

FashX aggregates fashion inventory from authorized partner feeds, normalizes raw merchant product records into canonical fashion garments, and maintains current offer pricing and stock status.

### 1. Data Normalization Hierarchy
- **`Merchant`**: The registered commercial entity (e.g., Myntra, Ajio, Zara).
- **`CatalogSource`**: The specific feed or API source, evaluated by the Catalog Quality Gate and cleared with `status="cleared"` and `rights_display=True`.
- **`MerchantProduct`**: The raw product record ingested from the partner feed, linked to a specific source and merchant.
- **`CanonicalGarment`**: The de-duplicated, normalized fashion item representing the core style, category, and visual attributes.
- **`MerchantOffer`**: The actionable purchase listing representing a specific merchant's price, stock availability, destination URL, and sync timestamp.

### 2. Catalog Source Clearance Enforcement
Commerce handoff is strictly restricted to products originating from cleared catalog sources:
```python
# Validation in CreateBuyClickUseCase
if source.status != "cleared":
    raise ValidationError("Catalog source is not cleared for commerce handoff")
if not source.rights_display:
    raise ValidationError("Catalog source does not have display rights")
```

Uncleared sources (such as `status="pending"`, `status="revoked"`, or `status="review"`) cannot be routed to outbound purchase handoffs.

### 3. Inactive Garment Protection
Garments marked as inactive (`active = False`) in the catalog:
- Are omitted from discovery feeds.
- Return `404 Not Found` when requested directly on `/catalog/garments/{id}`.
- Are rejected with `EntityNotFoundError` if a buy-click is attempted.
