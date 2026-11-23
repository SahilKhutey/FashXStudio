# Image Provenance and Metadata Standard

## 1. Provenance Data Model

Every stored image asset maintains complete provenance linking back to the origin merchant, source, contract evidence, and transformation history in `catalog_image_assets`:

```json
{
  "asset_id": "c1f72763-7eb5-4eb4-b6c2-b7e68bfeb619",
  "source_id": "97b39a3f-1d41-4770-ae32-5256e2978f80",
  "merchant_id": "845c4323-9568-45a7-b2eb-d115b3c53578",
  "source_product_id": "MERCHANT-SKU-100",
  "source_variant_id": "VAR-01",
  "source_reference": "https://approved.merchant.example/images/item100.jpg",
  "source_reference_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "original_sha256": "69324e9ecba9e746a6744883906b3a99fae5e6e30097fc18aa7bc1a1f5926ec3",
  "normalized_sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
  "perceptual_hash": "a1b2c3d4e5f60718",
  "original_mime_type": "image/jpeg",
  "original_width": 1200,
  "original_height": 1600,
  "original_bytes": 482910,
  "permission_evidence_id": "3b29c922-fdf4-4632-a589-98124b1fec9a",
  "permission_revision": 1,
  "permission_policy_version": "v1",
  "status": "ACTIVE",
  "quality_score": "PASS"
}
```

---

## 2. Invariant: Secret Sanitization

Sanitized URLs:
- Source references stored in `source_reference` strip authentication tokens, pre-signed credentials, and secret headers.
- Ephemeral SAS or S3 tokens are never persisted into relational tables.
