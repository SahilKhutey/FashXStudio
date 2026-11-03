# RC-01 — API Contracts & Schema Inventory

## Authoritative OpenAPI Baseline
An authoritative snapshot of the live API contract was generated during RC-01:
- File path: `audit/reports/rc01/openapi.json`
- Total registered endpoint paths: 222
- OpenAPI Specification Version: 3.1.0
- Application Title: FashX API

## Core Verified Endpoints

### 1. Feed & Personalization (`/api/v1/feed`)
- `GET /api/v1/feed`
  - Query parameters: `limit` (int, default 20), `cursor` (string, optional).
  - Headers: `Authorization: Bearer <token>`
  - Response Schema:
    ```json
    {
      "items": [
        {
          "canonical_garment_id": "uuid",
          "merchant_product_id": "uuid",
          "merchant_offer_id": "uuid",
          "title": "string",
          "brand": "string",
          "category": "top | bottom | one_piece | outerwear | footwear | accessory",
          "price_cents": 149900,
          "currency": "INR",
          "image_urls": ["string"],
          "stylist_explanation": "string"
        }
      ],
      "next_cursor": "string | null",
      "empty_reason": "catalog_empty | all_candidates_filtered | null"
    }
    ```

### 2. Wardrobe (`/api/v1/wardrobe/items`)
- `POST /api/v1/wardrobe/items`: Body `{"canonical_garment_id": "uuid"}` -> `201 Created`
- `GET /api/v1/wardrobe/items`: Returns array of `WardrobeItemRead` -> `200 OK`
- `DELETE /api/v1/wardrobe/items/{id}`: Returns `204 No Content`

### 3. Profile & Preferences (`/api/v1/profile/preferences`)
- `PUT /api/v1/profile/preferences`
  - Body:
    ```json
    {
      "categories": ["top", "bottom"],
      "budget_max": 500000,
      "gender": "women"
    }
    ```
- `GET /api/v1/profile/preferences`: Returns active profile preferences.

## Mobile Client Contract Discrepancies (For RC-02 Resolution)

| Field | Backend Expectation | Mobile Client Payload (`mobile/app/onboarding/profile.tsx`) | Impact | RC-02 Remediation |
| :--- | :--- | :--- | :--- | :--- |
| `categories` | Canonical categories: `top`, `bottom`, `one_piece`, `footwear` | Passed `v.occasions` (`casual`, `work`, `party`) | 100% of feed candidates filtered out | Map mobile UI to actual canonical categories |
| `budget_max` | Minor units (e.g. Paisa: `500000` = ₹5,000) | Rupees integer (`5000`) | Garments priced ₹1,499 (`149900`) filtered out | Multiply rupee input by 100 before API submission |
| `occasions` | Separate field in profile preferences | Overloaded into `categories` | Loss of occasion semantic filter | Send `occasions` in designated preference field |
