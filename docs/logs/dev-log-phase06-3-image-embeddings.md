# Dev Log: Phase 06.3 — Image Embeddings

## Date: 2026-11-21
## Author: AI Assistant (Antigravity)
## Branch: `feat/phase04.5-photo-upload`
## Scope: Phase 06.3 — Fashion Image Embedding Subsystem, Model Adapters, Preprocessing, Vector Store, Retrieval, and Blue/Green Migrations

---

### Objectives
Build a reliable, permission-aware image-embedding subsystem that converts authorized fashion product images into versioned numerical vectors, stores them efficiently in PostgreSQL with `pgvector` (with SQLite fallback for local test execution), and makes them searchable through nearest-neighbor similarity retrieval:
1. Model evaluation & ADR 0006 approving OpenCLIP ViT-B/32 (512 dimensions, L2-normalized) as primary baseline.
2. Formal model registry and governance (`docs/fashion-intelligence/embeddings/MODEL_APPROVAL_REGISTER.md`).
3. Vendor-neutral adapter interface (`ImageEmbeddingAdapter`) decoupling inference from storage and business logic.
4. Deterministic image preprocessing pipeline enforcing dimension bounds (100x100 to 4096x4096px, max aspect ratio 4:1), EXIF orientation correction, RGB normalization, and aspect-ratio preserved canvas padding.
5. Strict vector validation verifying 512 dimensions, finite floating-point numbers (no NaN or Inf), non-zero norm, and unit length.
6. Relational database persistence using PostgreSQL `pgvector` with HNSW vector indexing (`0047_add_image_embeddings.py`).
7. Dynamic permission enforcement verifying `IMAGE_AI_PROCESS` prior to image reading or inference.
8. Nearest-neighbor similarity retrieval supporting catalog visibility filtering, takedown exclusion, and merchant scoping.
9. Blue/green zero-downtime model migration with dual-write phase, backfill support, and canary rollback.
10. Fault-tolerant batch processing and retry queue with exponential backoff and dead-letter queuing.
11. Comprehensive test suite covering acceptance criteria EMB-001 through EMB-024.
12. 18 documentation deliverables under `docs/fashion-intelligence/embeddings/`.

---

### Architecture & Implementation Highlights
1. **Model Adapters (`backend/fashx/catalog/embeddings/`)**:
   - `base.py`: Defines `EmbeddingModelMetadata` and `ImageEmbeddingAdapter` protocol.
   - `models/mock_adapter.py`: Deterministic hash-seeded adapter generating reproducible 512-dim unit vectors for fast testing and CI.
   - `models/openclip_adapter.py`: Production OpenCLIP ViT-B/32 adapter supporting image and text encoding with L2 normalization.
   - `registry.py`: Singleton `EmbeddingModelRegistry` tracking approved models and managing adapter lifecycles.
2. **Preprocessing & Validation**:
   - `preprocessing.py`: Pillow-based image transformer handling EXIF transposition, bounds validation, color space normalization (RGBA/Grayscale -> RGB), and bicubic aspect-ratio preserved scaling with neutral padding.
   - `validation.py`: `validate_vector_invariants` enforcing dimension equality, numerical finiteness, non-zero norm, and unit norm.
3. **Database Models & Alembic Migration**:
   - `database/models/catalog_embeddings.py`: Defined 5 SQLAlchemy models (`EmbeddingModelRegistryRecord`, `ProductImageEmbeddingRecord`, `EmbeddingBatchRecord`, `EmbeddingJobRecord`, `EmbeddingMigrationRecord`).
   - `database/migrations/versions/0047_add_image_embeddings.py`: Alembic revision creating tables, unique constraints, lookup indexes, and PostgreSQL HNSW index with cosine distance operator (`vector_cosine_ops`).
4. **Service, Retrieval, Migration, and Batch Workers**:
   - `service.py`: `CatalogImageEmbeddingService` dynamically checks `IMAGE_AI_PROCESS` permission, verifies content SHA-256 against image asset records, runs preprocessing, executes adapter inference, validates output, and upserts embedding records.
   - `retrieval.py`: `VisualSimilarityRetriever` executes cosine distance search with active catalog visibility filters and automatic exclusion of assets under takedown.
   - `migration.py`: `ModelMigrationManager` orchestrates blue/green migration, canary evaluation, atomic cutover, and instant rollback.
   - `jobs/batch.py` & `jobs/retry.py`: Batch processor and retry handler managing job states, backoff delays with jitter, and dead-letter queue records.

---

### Verification & Testing
- Embedding Unit & Integration Tests:
  ```
  python -m pytest tests/unit/catalog/embeddings/ tests/integration/catalog/test_phase06_3_embeddings_database.py -v
  25 passed in 9.98s
  ```
- Acceptance Criteria Verified:
  - `EMB-001`: Approved model registry contains OpenCLIP ViT-B/32
  - `EMB-002`: Adapter implements `ImageEmbeddingAdapter` protocol
  - `EMB-003`: Generated vectors have exactly 512 dimensions
  - `EMB-004`: Vectors are strictly L2-normalized ($\|v\|_2 = 1.0 \pm 10^{-4}$)
  - `EMB-005`: Rejects vectors containing NaN or Inf values
  - `EMB-006`: Rejects zero-norm vectors
  - `EMB-007`: Repeated embeddings of identical image yield identical vectors
  - `EMB-008`: Rejects images below 100x100 or exceeding aspect ratio 4:1
  - `EMB-009`: Normalizes EXIF orientation correctly
  - `EMB-010`: Aspect ratio preserved with neutral padding on square canvas
  - `EMB-011`: Color space converted to 3-channel RGB
  - `EMB-012`: Preprocessing safely rejects corrupt or truncated image bytes
  - `EMB-013`: Persists embedding vector in `product_image_embeddings`
  - `EMB-014`: Enforces uniqueness on `(image_asset_id, model_id, model_version)`
  - `EMB-015`: Blocks embedding when `IMAGE_AI_PROCESS` permission is absent
  - `EMB-016`: Fails if image SHA-256 does not match asset records
  - `EMB-017`: Cosine retrieval ranks closest vector top
  - `EMB-018`: Similarity search excludes inactive or takedown-flagged assets
  - `EMB-019`: Blue/green model migration cutover
  - `EMB-020`: Canary rollback restores source model vectors
  - `EMB-021`: Batch processing creates batch records and jobs in order
  - `EMB-022`: Exponential backoff increases delay with jitter on transient failures
  - `EMB-023`: Permanent failure records error in DLQ (`embedding_jobs`)
  - `EMB-024`: Legacy `FakeEmbedder` and `ImageTextEmbedder` imports succeed
