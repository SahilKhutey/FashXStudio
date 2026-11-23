# Unified Search API Specification

## 1. Endpoints Overview
Mounted at `/api/v1/search/*`:

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/api/v1/search/products` | Unified keyword & structured filter search |
| `POST` | `/api/v1/search/semantic` | Natural language semantic search |
| `POST` | `/api/v1/search/visual` | Image reference similarity search |
| `GET` | `/api/v1/search/suggestions` | Autocomplete / query suggestions |
| `GET` | `/api/v1/search/facets` | Facet counts & filter metadata |
| `GET` | `/api/v1/search/sessions/{id}`| Retrieve a stable paginated search page |
| `POST` | `/api/v1/search/events` | Record shopper interaction events |

---

## 2. Request & Response Contracts

### 2.1 Keyword & Filter Search (`GET /api/v1/search/products`)
**Parameters**:
- `q`: string (max 200 chars)
- `category_id`: UUID
- `brand_id`: UUID
- `color_id`: UUID
- `occasion_id`: UUID
- `size`: string (e.g. "M", "38")
- `min_price`: Decimal (>= 0)
- `max_price`: Decimal (>= 0)
- `currency`: string (3-letter ISO code, default: "INR")
- `in_stock`: boolean
- `sort`: string allowlist (`relevance`, `price_low`, `price_high`, `newest`, `recently_updated`, `popularity`)
- `limit`: integer (1 to 50, default 20)
- `cursor`: string (opaque token)

**Response Schema**:
```json
{
  "search_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "query": "black casual shirt",
  "items": [
    {
      "product_id": "c0a80101-0000-0000-0000-000000000001",
      "merchant_product_id": "c0a80101-0000-0000-0000-000000000002",
      "title": "Men's Black Casual Shirt",
      "brand": {
        "id": "c0a80101-0000-0000-0000-000000000003",
        "name": "Roadster"
      },
      "price": {
        "amount": "899.00",
        "currency": "INR"
      },
      "availability": "IN_STOCK",
      "matched_attributes": ["black", "shirt", "casual"],
      "primary_image_url": "https://storage.fashx.com/catalog/thumb.webp"
    }
  ],
  "total": 12,
  "next_cursor": "ZXlKaGJHY2lPaUpJVXpJMU5pSXNJblI1Y0NJNklrcFhWQ0o5...",
  "applied_filters": {
    "size": "M",
    "in_stock": true
  },
  "facets": {},
  "sort": "relevance"
}
```
