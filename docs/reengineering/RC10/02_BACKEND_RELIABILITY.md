# RC10-B: Backend Performance and Reliability

## 1. Reliability Objectives
The goal of backend optimization is to ensure deterministic performance, resilient error recovery, and robust connection management without introducing unnecessary microservice complexity.

## 2. Engineering Targets (Target SLAs)
| Metric | Beta Target | Method / Tool |
| :--- | :--- | :--- |
| Normal Read API p95 | $\le 800\text{ ms}$ | `rc10_timing.py` & Prometheus tracing |
| Normal Write API p95 | $\le 1200\text{ ms}$ | `rc10_timing.py` & Prometheus tracing |
| API 5xx Error Rate | $< 0.1\%$ | Structured error middleware |
| Worker Retry Backoff | Exponential ($2^n\text{ s}$, max 3) | Async retry loop |
| Connection Pooling | Min 5, Max 20 connections | SQLAlchemy `asyncpg` pool configuration |

## 3. Synchronous Profiling Utility
For deterministic unit tests and internal profiling, [`backend.fashx.core.rc10_timing`](file:///c:/Users/ASUS/Documents/FashXStudio/backend/fashx/core/rc10_timing.py) provides `measure_call`:
```python
from fashx.core.rc10_timing import measure_call

value, timing = measure_call(lambda: compute_ranking())
# timing.duration_ms holds execution time in milliseconds
```

## 4. Query Profiling & Indexing Standards
- Avoid unindexed joins between `canonical_garments`, `merchant_products`, and `garment_enrichments`.
- Use pgvector HNSW indexing (`relaxed_order` iterative scanning) for 512-dimension vector similarity queries.
- Prevent N+1 query patterns by using `selectinload` or joined queries in SQL repositories.
