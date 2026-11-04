# RC07 — Embedding Persistence & Provenance

## 1. Schema Baseline
- **Table**: `garment_enrichments` (`database/models/catalog.py`)
- **Key Columns**:
  - `embedding`: 512-dimensional vector (`Vector512(512)` / pgvector in PostgreSQL, custom variant in SQLite).
  - `embedding_model`: `String(128)`, indexed.
  - `model_version`: `String(64)`.
  - `attributes_json`: `JSON` (structured garment attributes).

## 2. Versioned Persistence Protocol
The `embedding_model` string stores the full composite model key:
`<model_id>:<model_version>`

Examples:
- Production: `Marqo/marqo-fashionCLIP:2026.1`
- Test/Dev: `mock-fake-512:mock-v1`

## 3. Batch Embedding Script
- **Script**: `scripts/catalog/embed_garments.py`
- Loads catalog garments with primary images where `embedding_model != target_model` or `embedding IS NULL`.
- Supports `--dry-run` and `--apply` flags.
- Re-running with the identical model revision skips already processed garments idempotently.

## 4. Verification
Integration test `tests/integration/test_rc07_embedding_persistence.py` verifies:
- Dry-run detects un-embedded garments without modifying database.
- Apply step persists 512-dim normalized vector and `<model_id>:<model_version>` key.
- Subsequent run detects 0 garments needing embedding.
