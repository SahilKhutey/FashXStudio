# Shopper Profile API Contract

All profile endpoints are mounted under `/api/v1/profile` and require authentication (`Authorization: Bearer <token>`).

## 1. Endpoints Summary

| Method | Path | Summary | Success Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/profile/me` | Retrieve authenticated shopper profile | `200 OK` |
| `PUT` | `/api/v1/profile/me` | Create or completely replace profile | `200 OK` |
| `PATCH`| `/api/v1/profile/me` | Partially update profile attributes | `200 OK` |
| `GET` | `/api/v1/profile/me/completeness` | Evaluate feature-based profile readiness | `200 OK` |
| `GET` | `/api/v1/profile/me/category-sizes`| Retrieve category specific sizing | `200 OK` |
| `PUT` | `/api/v1/profile/me/category-sizes`| Replace category specific sizing | `200 OK` |

---

## 2. Request / Response Contracts

### 2.1 `GET /api/v1/profile/me`
Retrieves the profile of the current authenticated user. If no profile exists, an initial blank profile with `version: 1` is auto-created.

**Response `200 OK`**:
```json
{
  "id": "e305e608-8f5b-4399-bebe-0ef16298533c",
  "user_id": "98765432-1000-4000-8000-000000000001",
  "height_cm": 178.5,
  "weight_kg": 72.0,
  "preferred_size_system": "IN",
  "preferred_fit": "REGULAR",
  "style_preferences": ["CASUAL", "FORMAL"],
  "preferred_colors": ["NAVY", "BLACK"],
  "product_categories": ["TOPS", "BOTTOMS"],
  "shopping_preferences": {
    "budget": { "min": 1000, "max": 4000, "currency": "INR" },
    "shopping_intents": ["WORKWEAR", "EVERYDAY_WEAR"],
    "preferred_brands": ["Zara", "FabIndia"]
  },
  "category_sizes": [
    { "category_code": "TOPS", "size_system": "INTL", "size_label": "M" }
  ],
  "version": 1,
  "created_at": "2026-11-15T05:00:00Z",
  "updated_at": "2026-11-15T05:00:00Z"
}
```

---

### 2.2 `PUT /api/v1/profile/me`
Creates or fully updates the profile.

**Request Body**:
```json
{
  "height_cm": 175.0,
  "weight_kg": 70.0,
  "preferred_size_system": "IN",
  "preferred_fit": "REGULAR",
  "style_preferences": ["CASUAL"],
  "preferred_colors": ["BLUE", "WHITE"],
  "product_categories": ["TOPS"]
}
```

---

### 2.3 `PATCH /api/v1/profile/me`
Partially updates fields. Omitted fields are preserved. Passing `null` explicitly clears optional fields.

**Request Body**:
```json
{
  "preferred_fit": "SLIM",
  "expected_version": 1
}
```

**Conflict Response `409 Conflict`**:
```json
{
  "title": "conflict",
  "code": "conflict",
  "detail": "Profile version conflict detected. Please reload latest profile."
}
```

---

### 2.4 `GET /api/v1/profile/me/completeness`
Calculates dynamic feature readiness.

**Response `200 OK`**:
```json
{
  "overall_status": "PARTIAL",
  "overall_percentage": 80,
  "features": {
    "product_discovery": { "ready": true, "missing_fields": [] },
    "personalized_recommendations": { "ready": true, "missing_fields": [] },
    "size_guidance": { "ready": true, "missing_fields": [] },
    "fit_recommendation": { "ready": true, "missing_fields": [] },
    "advanced_vto": { "ready": false, "missing_fields": ["height_cm"] }
  }
}
```
