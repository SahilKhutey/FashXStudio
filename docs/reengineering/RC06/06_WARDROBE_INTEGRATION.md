# RC-06 — Wardrobe Persistence Integration

## User Wardrobe (Digital Closet) Integration

The Wardrobe subsystem allows authenticated users to save garments they love or intend to purchase later, creating a personalized digital closet that works seamlessly alongside Virtual Try-On (RC-05) and retailer offers (RC-06).

### Lifecycle Endpoints (`/wardrobe/items`)

| Method | Endpoint | Description | Scope |
|---|---|---|---|
| `POST` | `/wardrobe/items` | Save garment to wardrobe with optional offer link | Authenticated User |
| `GET` | `/wardrobe/items` | List user's saved wardrobe items | Scoped to Caller |
| `DELETE` | `/wardrobe/items/{garment_id}` | Remove garment from user's wardrobe | Scoped to Caller |

### Snapshot Metadata Invariance
When saving a garment to the wardrobe, FashX captures an immutable snapshot of the garment title, price, and primary image at that specific moment in time:
- `snapshot_title`: Populated from `MerchantProduct.title` or `CanonicalGarment.display_name`.
- `snapshot_price_minor`: Populated from the selected `MerchantOffer.price_minor` or `garment.display_price`.
- `offer_id`: UUID reference to the selected merchant offer (if supplied).

This guarantees that price changes or merchant catalog updates do not alter the user's historical saved records.

### Cross-User Isolation
Wardrobe operations are strictly scoped to the authenticated caller's principal ID (`principal.user_id`). Users can never list, modify, or delete items belonging to another user's closet.
