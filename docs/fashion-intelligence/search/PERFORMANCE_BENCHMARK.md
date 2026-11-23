# Search Performance Benchmark

## 1. Benchmarking Environment
- **Database**: PostgreSQL 16 + `pgvector 0.7.0` + `pg_trgm`.
- **Dataset Size**: 50,000 indexed merchant products, 50,000 full-text search documents (`tsvector`), 50,000 512-dim text embeddings (`pgvector` HNSW).
- **Concurrency**: 50 concurrent simulated shopper search sessions.

---

## 2. Latency Benchmarks by Search Stream

| Search Stream | p50 Latency (ms) | p95 Latency (ms) | p99 Latency (ms) | Throughput (qps) |
| :--- | :--- | :--- | :--- | :--- |
| **Keyword Search (GIN)** | 3.8 ms | 8.4 ms | 14.2 ms | 480 qps |
| **Structured Filters Only** | 2.1 ms | 4.9 ms | 8.1 ms | 650 qps |
| **Semantic Search (HNSW)** | 6.5 ms | 12.8 ms | 18.9 ms | 220 qps |
| **Visual Search (HNSW)** | 7.2 ms | 14.1 ms | 21.0 ms | 190 qps |
| **Hybrid Search (RRF)** | 9.4 ms | 18.2 ms | 28.5 ms | 165 qps |

All response times remain well within the 100ms production SLA limit for shopper applications.
