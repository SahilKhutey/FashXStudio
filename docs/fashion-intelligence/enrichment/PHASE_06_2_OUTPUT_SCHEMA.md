# Phase 06.2 — Enrichment Output Schema Specification

## 1. Output Contract Overview

The enrichment output (`EnrichmentOutput`) delivers normalized fashion attributes, category mapping, confidence scores, evidence references, and review requirements.

## 2. Output Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "EnrichmentOutput",
  "type": "object",
  "required": [
    "schema_version",
    "product_id",
    "taxonomy_version",
    "enrichment_version",
    "status",
    "attributes",
    "evidence",
    "review"
  ],
  "properties": {
    "schema_version": { "type": "string", "default": "1.0.0" },
    "product_id": { "type": "string" },
    "taxonomy_version": { "type": "string" },
    "enrichment_version": { "type": "string", "default": "1.0.0" },
    "status": {
      "type": "string",
      "enum": ["QUEUED", "RUNNING", "COMPLETED", "PARTIAL", "REVIEW_REQUIRED", "FAILED", "REJECTED"]
    },
    "category_id": { "type": ["string", "null"] },
    "garment_type": { "type": ["string", "null"] },
    "attributes": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["status", "review_status"],
        "properties": {
          "value": {},
          "status": {
            "type": "string",
            "enum": ["KNOWN", "UNKNOWN", "CONFLICTING", "NOT_APPLICABLE", "NOT_PROVIDED"]
          },
          "confidence": { "type": ["number", "null"], "minimum": 0.0, "maximum": 1.0 },
          "source": {
            "type": ["string", "null"],
            "enum": ["MERCHANT", "RULE_BASED", "AI_TEXT", "AI_IMAGE", "HUMAN_REVIEW", "FALLBACK", null]
          },
          "review_status": {
            "type": "string",
            "enum": ["AUTO_ACCEPTED", "PENDING_REVIEW", "APPROVED", "REJECTED", "CORRECTED", "NOT_REQUIRED"]
          },
          "evidence_ids": { "type": "array", "items": { "type": "string" } },
          "flags": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "evidence": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["evidence_id", "evidence_type", "source_record_id"],
        "properties": {
          "evidence_id": { "type": "string" },
          "evidence_type": {
            "type": "string",
            "enum": [
              "MERCHANT_FIELD",
              "TITLE",
              "DESCRIPTION",
              "IMAGE_ASSET",
              "SOURCE_SPECIFICATION",
              "RULE_MATCH",
              "AI_TEXT_EXTRACTION",
              "AI_IMAGE_EXTRACTION",
              "HUMAN_CORRECTION"
            ]
          },
          "source_record_id": { "type": "string" },
          "source_revision": { "type": ["string", "null"] },
          "evidence_text": { "type": ["string", "null"] },
          "evidence_hash": { "type": ["string", "null"] },
          "start_offset": { "type": ["integer", "null"] },
          "end_offset": { "type": ["integer", "null"] },
          "extraction_method": { "type": ["string", "null"] }
        }
      }
    },
    "review": {
      "type": "object",
      "required": ["required", "reasons"],
      "properties": {
        "required": { "type": "boolean" },
        "reasons": { "type": "array", "items": { "type": "string" } }
      }
    },
    "idempotency_key": { "type": ["string", "null"] }
  },
  "additionalProperties": false
}
```
