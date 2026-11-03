# RC-01 — Wardrobe & Closet Recovery

## Problem Statement
In RC-00, the Closet screen was noted as an empty state. It was unverified whether wardrobe persistence, garment saving from the feed, snapshot preservation, or item deletion functioned end-to-end.

## Wardrobe Data Architecture

### 1. Snapshot Preservation Pattern
When a user saves a garment to their wardrobe, the backend persists an immutable snapshot:
- `canonical_garment_id`: References the canonical garment.
- `merchant_product_id`: Associated merchant product.
- `merchant_offer_id`: Active offer identifier.
- Snapshot columns: `title`, `brand`, `category`, `price_cents`, `currency`, `image_url`.
- Preservation invariant: If a merchant later updates or delists the product, the user's saved closet item retains its original price, image, and description as saved.

### 2. Endpoints & Operations
- `POST /api/v1/wardrobe/items`: Save a garment to the wardrobe.
- `GET /api/v1/wardrobe/items`: List all active saved items for the authenticated user.
- `DELETE /api/v1/wardrobe/items/{item_id}`: Remove a saved item from the wardrobe.

## Verification & Test Results

### 1. Live Runtime Verification
The following sequence was executed against the running FastAPI instance:

```python
# 1. Save garment
payload = {"canonical_garment_id": "00000000-0000-0000-0000-000000000001"}
headers = {"Authorization": "Bearer dev-user-1"}
res = requests.post("http://127.0.0.1:8000/api/v1/wardrobe/items", json=payload, headers=headers)
# Response: 201 Created -> item_id: ea7251ea-c4c0-4828-9860-2ff586fa6c5f

# 2. List items
res = requests.get("http://127.0.0.1:8000/api/v1/wardrobe/items", headers=headers)
# Response: 200 OK -> 1 item returned with correct title, price_cents, and image_url

# 3. Delete item
res = requests.delete("http://127.0.0.1:8000/api/v1/wardrobe/items/ea7251ea-c4c0-4828-9860-2ff586fa6c5f", headers=headers)
# Response: 204 No Content

# 4. Confirm deletion
res = requests.get("http://127.0.0.1:8000/api/v1/wardrobe/items", headers=headers)
# Response: 200 OK -> 0 items returned
```

### 2. Cross-User Isolation Verification
- Item saved under `dev-user-1` was queried with `Authorization: Bearer dev-user-2`.
- `dev-user-2` list query returned 0 items.
- Direct attempt by `dev-user-2` to delete `dev-user-1`'s item returned `404 Not Found`.
- Result: 🟢 Cross-user tenant isolation verified.

### 3. Automated Regression Suite
- `tests/unit/test_mvp5_closet_shopping_journey.py` passed (10 tests passing).
