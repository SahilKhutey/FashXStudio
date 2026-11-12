# Database Performance Baseline and Latency Specifications

## 1. Workload Performance Targets (SLAs)

The following service level objectives (SLOs) govern PostgreSQL query execution and connection pooling across FashXStudio:

| Operation Category | Specific Query / Use Case | P50 Target | P95 Target | P99 Target |
| :--- | :--- | :--- | :--- | :--- |
| **Simple Indexed Read** | `SELECT * FROM user_style_profiles WHERE user_id = $1` | < 10 ms | < 50 ms | < 100 ms |
| **Catalog Garment Retrieval** | `SELECT * FROM garments WHERE id = $1` | < 15 ms | < 60 ms | < 120 ms |
| **Wardrobe Listing (Paginated)**| `SELECT * FROM wardrobe_items WHERE user_id = $1 LIMIT 20` | < 25 ms | < 80 ms | < 150 ms |
| **VTO Job State Update** | `UPDATE tryon_jobs SET status = $1, output_url = $2 WHERE id = $3`| < 20 ms | < 80 ms | < 150 ms |
| **Saved Look Insertion** | `INSERT INTO saved_looks (...) VALUES (...)` | < 30 ms | < 100 ms | < 200 ms |
| **Vector Similarity Search** | `SELECT id FROM garments ORDER BY embedding <=> $1 LIMIT 10` | < 50 ms | < 150 ms | < 300 ms |
| **Connection Acquisition** | `pool.acquire()` wait time under normal load | < 5 ms | < 25 ms | < 100 ms |
| **Connection Establishment**| Initial TLS handshake to RDS endpoint in-VPC | < 100 ms | < 300 ms | < 500 ms |

---

## 2. Benchmark Script & Execution Protocol

FashXStudio includes a dedicated benchmarking utility at [`scripts/db/benchmark_postgres.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/db/benchmark_postgres.py).

### Execution Command
```bash
export DATABASE_URL="postgresql+asyncpg://fashx_staging_app:<SECRET>@db.staging.internal:5432/fashx_staging?ssl=require"
export DB_BENCH_CONCURRENCY=10
export DB_BENCH_ITERATIONS=100

python scripts/db/benchmark_postgres.py
```

### Measured Output Format
```text
==================================================================
FASHXSTUDIO DATABASE BENCHMARK
Concurrency : 10 workers
Iterations  : 100 queries / worker (Total: 1000)
==================================================================
Pool initialization (10 connections): 142.30 ms
------------------------------------------------------------------
Total Queries  : 1000
Total Duration : 1.84 s
Throughput     : 543.5 QPS
Mean Latency   : 1.81 ms
P50 Latency    : 1.62 ms
P95 Latency    : 3.40 ms
P99 Latency    : 5.12 ms
==================================================================
```

---

## 3. Query Optimization and Indexing Policy

1. **Mandatory Indexing**: All foreign keys (`user_id`, `garment_id`, `brand_id`) and search filters (`status`, `created_at`) must possess explicit B-Tree indexes defined in Alembic migrations.
2. **pgvector Indexing**:
   - Initial catalog datasets (<10,000 garments): Exact search (`<=>` cosine distance) provides <50ms response times without index overhead.
   - Scale catalog datasets (>10,000 garments): Add HNSW index (`USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)`) to maintain sub-50ms retrieval.
3. **Slow Query Logging**: The RDS parameter group sets `log_min_duration_statement=500`, automatically logging queries exceeding 500ms to CloudWatch for index analysis via `EXPLAIN (ANALYZE, BUFFERS)`.
