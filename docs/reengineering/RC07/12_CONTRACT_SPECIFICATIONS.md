# RC07 — API Contract Specifications

## 1. Overview
RC07 maintains backward and forward compatibility for all feed and personalization endpoints consumed by the Expo mobile application.

## 2. Endpoints
### A. `GET /api/v1/feed`
- **Query Parameters**:
  - `limit` (int, default: 20, 1..100)
  - `diversity` (float, default: 0.7, 0.0..1.0)
  - `cursor` (string | null)
- **Response**: `FeedResponse`
```json
{
  "user_id": "uuid",
  "items": [
    {
      "garment_id": "uuid",
      "category": "tops",
      "subcategory": "shirt",
      "price_minor": 3500,
      "dominant_color": "navy",
      "silhouette": "regular",
      "relevance_score": 0.88,
      "stylist_explanation": "Curated garment features flattering navy tones.",
      "title": "Navy Linen Shirt",
      "brand": "Studio Brand",
      "image_url": "https://...",
      "image": {
        "url": "https://...",
        "expires_at": "2026-11-04T12:00:00Z"
      },
      "price_updated_at": "2026-11-04T10:00:00Z",
      "reason_chips": ["Top Pick", "Navy Harmony", "In Your Size"],
      "tryon_supported": true
    }
  ],
  "total_candidates": 45,
  "filtered_candidates": 38,
  "next_cursor": "20",
  "relaxed": [],
  "empty_reason": null
}
```

### B. `POST /api/v1/feed/signals`
- **Status**: 201 Created
- **Request**:
```json
{
  "garment_id": "uuid",
  "action": "like"
}
```
- **Allowed Actions**: `"like"`, `"hide"`, `"not_interested"`
- **Response**:
```json
{
  "status": "recorded",
  "user_id": "uuid",
  "garment_id": "uuid",
  "action": "like"
}
```

## 3. Verification
Contract test `tests/contracts/test_rc07_recommendation_contract.py` validates response schema, status codes, field types, and bounds.
