# 05 — Validation Rules and Quarantine

## 1. Validation Pipeline

Every incoming size chart submission passes through the validation engine before reaching the database.

```mermaid
flowchart TD
    Payload[SizeChartRevisionCreate Payload] --> V1[Check 1: Required Fields & Provenance]
    V1 -->|Fail| Q[Quarantine Submission]
    V1 -->|Pass| V2[Check 2: Unique Size Labels & Fields]
    V2 -->|Fail| Q
    V2 -->|Pass| V3[Check 3: Field Registry & Range Bounds]
    V3 -->|Fail| Q
    V3 -->|Pass| V4[Check 4: Category Field Eligibility]
    V4 -->|Fail| Q
    V4 -->|Pass| V5[Check 5: Cross-Row Monotonic Progression]
    V5 -->|Warning / Pass| Publish[Publish Active Revision]
```

## 2. Validation Severity Levels

- **ERROR (Terminal)**: Blocks ingestion immediately, moves payload to quarantine table, and responds with HTTP 422.
  - Empty or non-positive measurements ($\le 0$).
  - Missing source provenance (missing `source_id`).
  - Duplicate size labels in the same chart (e.g., two "M" rows).
  - Duplicate measurement fields in the same row (e.g., two "CHEST" fields).
  - Unknown measurement field codes not in `FIELD_DEFINITIONS`.
  - Values outside physical plausible limits (e.g. Chest < 40 cm or > 200 cm).
  - Category incompatibility (e.g. Inseam provided on a Dress or Top).
- **WARNING (Non-blocking)**: Logged as an ingestion warning without blocking publishing.
  - Inverted dimension progression across ascending sizes (e.g., Size L chest is smaller than Size M chest). While unusual, bespoke or relaxed fits may feature varying dimensions.

## 3. Quarantine Workflow (`size_chart_quarantine`)

When a submission is quarantined:
1. The exact raw payload is saved in `size_chart_quarantine.raw_payload_json`.
2. A list of all failed error codes is preserved in `error_codes_json`.
3. `review_status` defaults to `PENDING`.
4. The product size chart container remains in its previous valid state or `UNAVAILABLE`.
5. Merchant ops can inspect quarantined charts via internal tooling and request merchant re-export.
