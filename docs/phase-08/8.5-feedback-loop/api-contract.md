# Phase 08.5 API Contract

| Method | Path | Purpose |
|---|---|---|
| `PUT` | `/api/v1/products/{product_id}/reaction` | Set `LIKE`, `DISLIKE`, or `NONE` idempotently |
| `GET` | `/api/v1/products/{product_id}/reaction` | Read current shopper reaction |
| `PUT` | `/api/v1/products/{product_id}/saved` | Save product idempotently |
| `DELETE` | `/api/v1/products/{product_id}/saved` | Unsave product |
| `GET` | `/api/v1/products/{product_id}/saved` | Read current saved state |
| `POST` | `/api/v1/feedback/events` | Ingest registered feedback/interaction event (`202 Accepted`) |
| `POST` | `/api/v1/tryon/jobs/{job_id}/feedback` | Submit VTO visual quality feedback |
| `POST` | `/api/v1/merchant-offers/{offer_id}/outbound` | Record merchant outbound redirect intent |
| `GET` | `/api/v1/feedback/consents` | List current purpose-specific consents |
| `PUT` | `/api/v1/feedback/consents/{purpose}` | Grant or withdraw purpose-specific consent |
| `DELETE` | `/api/v1/shopper/preferences` | Clear personalization projections & invalidate cache |
| `GET` | `/api/v1/feedback/metrics` | Read feedback pipeline & bias monitoring metrics |
