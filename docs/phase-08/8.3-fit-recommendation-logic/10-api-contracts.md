# 10 — API Contracts (`backend/fashx/fit/router.py`)

All endpoints require authentication via `get_principal` (`Authorization: Bearer <token>`) mounted at `/api/v1/fit`.

| Method | Endpoint | Purpose | Success Codes | Error Codes |
|---|---|---|---|---|
| `POST` | `/api/v1/fit/recommendations` | Evaluate size recommendation server-side | `200` (including abstentions) | `401`, `404`, `422`, `429`, `500` |
| `GET` | `/api/v1/fit/recommendations/{recommendation_id}` | Fetch owned recommendation snapshot | `200` | `401`, `403`, `404`, `422` |
| `POST` | `/api/v1/fit/recommendations/{recommendation_id}/feedback` | Submit owner-bound feedback | `201` | `401`, `403`, `404`, `409`, `422` |
| `GET` | `/api/v1/fit/recommendations/{recommendation_id}/feedback` | Retrieve own feedback | `200` | `401`, `403`, `404`, `422` |
| `GET` | `/api/v1/products/{product_id}/size-chart` | Retrieve Phase 08.1 merchant chart | `200` | `401`, `404` |

`FitRecommendationRequest` sets `extra="forbid"`, rejecting client-supplied `shopper_id`, `measurements`, `confidence`, or `authorized` flags at validation (`422`). Business abstentions (`INSUFFICIENT_INFORMATION`, `UNSUPPORTED_CATEGORY`, `STALE_DATA`, `CONFLICTING_DATA`, `NO_AVAILABLE_SIZE`) are valid `200 OK` domain responses rather than `5xx` errors.
