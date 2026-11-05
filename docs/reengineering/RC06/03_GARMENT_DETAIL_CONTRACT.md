# RC-06 — Garment Detail Contract Specification

## Endpoint: `GET /catalog/garments/{id}`

Retrieves the consumer-facing canonical garment detail including metadata, stock status, category classification, and all associated retailer offers.

### Request
- **Method:** `GET`
- **Path:** `/catalog/garments/{id}`
- **Headers:** `Authorization: Bearer <jwt_token>`

### Response Schema (`CustomerGarmentDetail`)

```json
{
  "id": "c1f73719-74d1-4e78-9e6a-29759c381c81",
  "title": "Relaxed Linen Resort Shirt Navy",
  "brand_name": "Harbour & Bay",
  "category": "tops",
  "subcategory": "shirts",
  "gender": "men",
  "price_minor": 179900,
  "currency": "INR",
  "images": [
    "https://storage.fashx.com/garments/c1f73719/primary.jpg"
  ],
  "tryon_supported": true,
  "sizes_in_stock": ["S", "M", "L", "XL"],
  "offers": [
    {
      "id": "e6a17b08-360b-4682-959c-6b3a36db8a1f",
      "merchant_id": "8c5da84f-e18e-4903-8839-a9a34bc14d64",
      "merchant_name": "Myntra",
      "price_minor": 179900,
      "currency": "INR",
      "in_stock": true,
      "updated_at": "2026-11-04T08:00:00Z"
    },
    {
      "id": "b3e21c97-6a45-420a-8d19-4c281d77f802",
      "merchant_id": "72f1aa02-140a-48d5-bd84-38cfa8201b13",
      "merchant_name": "Ajio",
      "price_minor": 199900,
      "currency": "INR",
      "in_stock": true,
      "updated_at": "2026-11-04T08:00:00Z"
    },
    {
      "id": "f9a56201-9a7c-48be-a6b1-0482591fa308",
      "merchant_id": "18f50aa1-5a20-4109-b690-671239aa412e",
      "merchant_name": "Tata CLiQ",
      "price_minor": 149900,
      "currency": "INR",
      "in_stock": false,
      "updated_at": "2026-11-04T08:00:00Z"
    }
  ]
}
```

### Contract Rules & Invariants
1. `price_minor`: Always an integer representing minor units (paise for INR, cents for USD). Never a float.
2. `offers`: Strictly ranked with in-stock offers first, followed by price ascending.
3. `offers[].updated_at`: Real timestamp derived directly from `MerchantOffer.last_synced_at`. Never a synthetic timestamp.
4. `offers[].merchant_name`: Resolved from the `merchants` table via foreign key; falls back to `"Authorized Retailer"` on the client if absent.
5. `extra="forbid"`: Both `CustomerGarmentDetail` and `CustomerOfferDetail` Pydantic models forbid unexpected fields to maintain contract stability.
