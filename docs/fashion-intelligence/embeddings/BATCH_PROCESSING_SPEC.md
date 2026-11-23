# Fashion Image Embedding Batch Processing Specification

## 1. Objective
Enable high-throughput, fault-tolerant batch embedding generation for catalog ingestion runs, periodic synchronization, and full catalog re-indexing.

---

## 2. Batch Execution Architecture

```mermaid
flowchart LR
    QUEUE[Pending Image Assets] --> PARTITION[Batch Partitioner]
    PARTITION --> BATCH[Batch of N Images: 16 to 64]
    BATCH --> PRE_POOL[Concurrent Preprocessor Pool]
    PRE_POOL --> STACK[Stacked Tensor Batch]
    STACK --> GPU[Batched Adapter Inference]
    GPU --> VEC_VAL[Batch Vector Validation]
    VEC_VAL --> BULK_INSERT[(PostgreSQL pgvector Bulk Insert)]
    BULK_INSERT --> ACK[Batch Checkpoint Ack]
```

---

## 3. Batch Parameters and Sizing
- **Default Batch Size**: 32 images (configurable from 16 to 64 depending on worker GPU/CPU memory).
- **Concurrency**: Parallel image fetch and preprocessing (I/O bound) decoupled from batch model inference (compute bound).
- **Idempotency Key**: `batch_key = sha256(f"{model_id}:{model_version}:{sorted_asset_ids}")`.
- If a batch crashes mid-way, records already inserted are preserved; unprocessed items are picked up on the next worker pass.

---

## 4. Backpressure and Memory Control
- Maximum queued in-flight batches per worker: 4 batches (prevents unbounded memory growth if database write throughput degrades).
- Generator-based streaming iteration over database query cursors to avoid loading entire catalog image lists into memory.
