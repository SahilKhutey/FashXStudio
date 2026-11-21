# Fashion Image Embedding Implementation & Operations Runbook

## 1. Overview
This runbook guides engineers and operators through deploying, configuring, monitoring, and migrating the Fashion Image Embedding Subsystem.

---

## 2. Environment Configuration
Ensure the following environment variables are configured:
```bash
# Model settings
EMBEDDING_MODEL_ID="openclip_vit_b32"
EMBEDDING_MODEL_VERSION="v1"
EMBEDDING_MODEL_DEVICE="cuda" # or "cpu"

# Batch settings
EMBEDDING_BATCH_SIZE=32
EMBEDDING_MAX_WORKERS=4

# Retrieval settings
VECTOR_SEARCH_EF=40
VECTOR_SEARCH_DEFAULT_LIMIT=20
VECTOR_SEARCH_MIN_SIMILARITY=0.60
```

---

## 3. Database Migration Deployment
1. Run Alembic upgrade to apply table schema:
   ```bash
   alembic upgrade head
   ```
2. Verify table creation in PostgreSQL:
   ```sql
   SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%embedding%';
   ```
3. Verify HNSW index status:
   ```sql
   SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'product_image_embeddings';
   ```

---

## 4. Operational Monitoring & Health Checks
- **Queue Lag**: Monitor count of pending records in `embedding_jobs` (`status = 'PENDING'`).
- **Error Rate**: Monitor ratio of `FAILED` jobs to completed jobs over rolling 1-hour window.
- **Inference Latency**: Track p95 inference time per batch (target: <50ms on GPU, <500ms on CPU).
- **Index Latency**: Track nearest-neighbor query execution time in PostgreSQL logs.

---

## 5. Blue/Green Model Migration Procedure
When deploying a new model version:
1. Register new model in `embedding_model_registry`.
2. Enable dual write in ingestion pipeline.
3. Start background backfill job:
   ```bash
   python -m fashx.catalog.embeddings.cli migrate-backfill --target-model-id <new_id> --target-version <new_ver>
   ```
4. Perform canary query validation on 10% search sample.
5. Execute cutover command:
   ```bash
   python -m fashx.catalog.embeddings.cli cutover --model-id <new_id> --version <new_ver>
   ```
6. Monitor error rates for 24 hours before retiring old model checkpoint.
