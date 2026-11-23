# Phase 06.2 — Enrichment Input Schema Specification

## 1. Input Contract Overview

The input contract (`EnrichmentInput`) provides a normalized, read-only payload consumed by the enrichment pipeline regardless of whether the product originated from direct API feeds, partner catalogs, or CSV exports.

## 2. JSON Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "EnrichmentInput",
  "type": "object",
  "required": [
    "schema_version",
    "product_id",
    "merchant_id",
    "source_id",
    "source_product_id",
    "taxonomy_version",
    "content"
  ],
  "properties": {
    "schema_version": { "type": "string", "default": "1.0.0" },
    "product_id": { "type": "string", "format": "uuid" },
    "merchant_id": { "type": "string", "format": "uuid" },
    "source_id": { "type": "string", "format": "uuid" },
    "source_product_id": { "type": "string" },
    "taxonomy_version": { "type": "string" },
    "source_revision": { "type": ["string", "null"] },
    "content": {
      "type": "object",
      "required": ["title"],
      "properties": {
        "title": { "type": "string", "minLength": 1 },
        "description": { "type": ["string", "null"] },
        "merchant_category": { "type": ["string", "null"] },
        "brand": { "type": ["string", "null"] },
        "attributes": { "type": "object" },
        "variants": { "type": "array" },
        "size_information": { "type": ["object", "null"] }
      }
    },
    "images": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["asset_id"],
        "properties": {
          "asset_id": { "type": "string" },
          "asset_url": { "type": ["string", "null"] },
          "image_type": { "type": "string", "default": "PRIMARY" },
          "has_ai_permission": { "type": "boolean", "default": false }
        }
      }
    },
    "permissions": {
      "type": "object",
      "properties": {
        "text_processing": { "type": "boolean", "default": true },
        "image_ai_processing": { "type": "boolean", "default": false },
        "vto_processing": { "type": "boolean", "default": false }
      }
    }
  },
  "additionalProperties": false
}
```

## 3. Data Integrity Constraints

- `product_id` and `taxonomy_version` must be non-empty.
- `title` cannot be empty or contain only whitespace.
- Original merchant field values are preserved without modification.
- Image assets are referenced only by verified internal asset IDs, never untrusted third-party URLs.
