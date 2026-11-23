# Fashion Image Similarity Retrieval API Specification

## 1. Overview
The Similarity Retrieval API provides nearest-neighbor search across catalog product embeddings, filtering by visibility, merchant scope, and inventory status.

---

## 2. API Endpoints

### 2.1 Search by Reference Image Vector
- **Method**: `POST`
- **Path**: `/api/v1/catalog/embeddings/search/vector`
- **Request Body**:
  ```json
  {
    "vector": [0.034, -0.012, ..., 0.089],
    "model_id": "openclip_vit_b32",
    "model_version": "v1",
    "limit": 20,
    "min_similarity": 0.65,
    "filter": {
      "merchant_ids": ["c0a80101-0000-0000-0000-000000000001"],
      "categories": ["apparel/tops/t_shirt"],
      "in_stock_only": true
    }
  }
  ```
- **Response**:
  ```json
  {
    "query_model": "openclip_vit_b32:v1",
    "total_matched": 12,
    "results": [
      {
        "product_id": "4b5d6e7f-8a9b-0c1d-2e3f-4a5b6c7d8e9f",
        "image_asset_id": "3a4b5c6d-7e8f-9a0b-1c2d-3e4f5a6b7c8d",
        "similarity_score": 0.9412,
        "cosine_distance": 0.0588,
        "merchant_id": "c0a80101-0000-0000-0000-000000000001",
        "primary_image_url": "https://storage.fashx.com/catalog/thumb/3a4b5c.webp"
      }
    ]
  }
  ```

### 2.2 Search by Existing Catalog Image ID
- **Method**: `GET`
- **Path**: `/api/v1/catalog/embeddings/search/similar/{image_asset_id}`
- **Query Parameters**:
  - `limit`: Integer (default 20, max 100).
  - `min_similarity`: Float (default 0.6).
  - `exclude_same_product`: Boolean (default true).

---

## 3. Catalog Integrity & Visibility Filter Contract
Every nearest-neighbor search MUST enforce:
1. `pie.is_active = TRUE`: Only retrieve active vectors for the active model.
2. `cia.status = 'ACTIVE'`: Exclude images that are suspended, pending deletion, or rejected.
3. Exclude any image whose parent `merchant_id` or `source_id` is subject to an active takedown (`ImageTakedownStatus.PROCESSING` or `COMPLETED`).
4. Merchant visibility restrictions if the requesting tenant does not have cross-merchant viewing privileges.
