# Phase 08.4 API Contract

All shopper endpoints resolve identity strictly from the authenticated `Principal` (`get_principal`); client-supplied `shopper_id` or preference scores are never accepted.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/ranking/products` | Shopper (`get_principal`) | Personalized or baseline ranked eligible products |
| `POST` | `/api/v1/ranking/preview` | Admin (`require_role("admin")`) | Internal ranking preview |
| `GET` | `/api/v1/ranking/config` | Shopper (`get_principal`) | Active ranking version and weights |
| `POST` | `/api/v1/products/{product_id}/feedback` | Shopper (`get_principal`) | Submit explicit feedback (`LIKE`, `DISLIKE`, `SAVE`, `REMOVE_SAVED`, `NOT_INTERESTED`) |
| `GET` | `/api/v1/products/{product_id}/feedback` | Shopper (`get_principal`) | List shopper's active feedback for product |
| `DELETE` | `/api/v1/products/{product_id}/feedback` | Shopper (`get_principal`) | Withdraw explicit feedback |
| `GET` | `/api/v1/shopper/preferences` | Shopper (`get_principal`) | Retrieve shopper ranking preferences |
| `PATCH` | `/api/v1/shopper/preferences` | Shopper (`get_principal`) | Update preferences and increment revision |
