# Dataset Manifest Schema (JSONL)

## 1. Schema Definition

The benchmark manifest is stored as a line-delimited JSON (`JSONL`) file (e.g. `datasets/vto/manifest.v1.jsonl`). Each row defines a single evaluated person-garment pairing.

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "EvaluationPair",
  "type": "object",
  "required": [
    "pair_id",
    "dataset_version",
    "participant_id",
    "shopper_asset_id",
    "garment_asset_id",
    "canonical_product_id",
    "garment_category",
    "permission_record_id"
  ],
  "properties": {
    "pair_id": { "type": "string" },
    "dataset_version": { "type": "string" },
    "participant_id": { "type": "string" },
    "shopper_asset_id": { "type": "string", "format": "uuid" },
    "garment_asset_id": { "type": "string", "format": "uuid" },
    "canonical_product_id": { "type": "string", "format": "uuid" },
    "garment_category": { "type": "string" },
    "market": { "type": "string", "default": "IN" },
    "partition": { "type": "string", "enum": ["DEVELOPMENT", "VALIDATION", "HOLDOUT_TEST"] },
    "height_band": { "type": ["string", "null"] },
    "body_representation_group": { "type": ["string", "null"] },
    "skin_tone_annotation": { "type": ["string", "null"] },
    "lighting": { "type": "string" },
    "camera_distance": { "type": "string" },
    "pose": { "type": "string" },
    "difficulty": { "type": "string", "enum": ["STANDARD", "CHALLENGING", "NEGATIVE"] },
    "permission_record_id": { "type": "string" },
    "eligible_for_live_provider": { "type": "boolean" },
    "expected_outcome": { "type": "string", "enum": ["INFERENCE", "REJECT_INPUT", "NEEDS_REVIEW"] }
  },
  "additionalProperties": false
}
```

---

## 2. Integrity Checks

1. **No External URLs**: Manifests reference internal UUIDs (`shopper_asset_id`), never public S3 URLs or external HTTP endpoints.
2. **Deterministic Hashing**: The manifest file itself has its SHA-256 digest recorded in `tryon_evaluation_datasets` upon release freeze.
