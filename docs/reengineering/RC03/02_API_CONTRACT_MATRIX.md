# RC-03 — API Contract Matrix

This matrix formalizes the end-to-end integration contracts between the Expo mobile client and the FastAPI backend.

| Domain | Method | Endpoint | Request Payload / Params | Response Payload | Status |
|---|---|---|---|---|---|
| **Health** | GET | `/healthz/live` | None | `{ "status": "ok", "service": "...", "version": "..." }` | 200 |
| **Health** | GET | `/healthz/ready` | None | `{ "status": "ok", "database": "ok", "dependencies": {...} }` | 200 / 503 |
| **Identity** | GET | `/api/v1/me` | Bearer Token | `{ "user_id": UUID, "roles": [...], "onboarding": {...} }` | 200 |
| **Identity** | DELETE | `/api/v1/me` | Bearer Token | `{ "status": "queued" }` | 202 |
| **Discovery** | GET | `/api/v1/feed` | `?limit=20&cursor=...` | `{ "items": [FeedItem], "total": int }` | 200 |
| **Signals** | POST | `/api/v1/feed/signals` | `{ "garment_id": UUID, "action": "like"\|"hide"\|"not_interested" }` | `{ "status": "recorded" }` | 201 |
| **Commerce** | POST | `/api/v1/commerce/buy-clicks` | `{ "garment_id": UUID, "offer_id"?: UUID }` | `{ "buy_click_id": UUID, "redirect_url": str, "tracking_id": str }` | 201 |
| **Wardrobe** | POST | `/api/v1/wardrobe/items` | `{ "garment_id": UUID, "offer_id"?: UUID, "tryon_artifact_id"?: UUID }` | `{ "item_id": UUID, "garment_id": UUID, "snapshot_title": str, ... }` | 201 |
| **Wardrobe** | GET | `/api/v1/wardrobe/items` | `?limit=50&offset=0` | `[WardrobeItemView]` | 200 |
| **Wardrobe** | DELETE | `/api/v1/wardrobe/items/{id}` | Path param `id` | None | 204 |
| **Try-On** | POST | `/api/v1/tryon/jobs` | `{ "garment_id": UUID, "photo_id"?: UUID }` | `{ "job_id": UUID, "status": "queued"\|"completed", ... }` | 201 |
| **Try-On** | GET | `/api/v1/tryon/jobs` | `?limit=20` | `[TryOnJobView]` | 200 |
| **Try-On** | GET | `/api/v1/tryon/jobs/{id}` | Path param `id` | `{ "job_id": UUID, "status": str, "result_image_url": str, ... }` | 200 |

## OpenAPI Artifact
The complete machine-readable OpenAPI 3.1 specification is maintained at [openapi.json](file:///artifacts/rc03/openapi.json).
