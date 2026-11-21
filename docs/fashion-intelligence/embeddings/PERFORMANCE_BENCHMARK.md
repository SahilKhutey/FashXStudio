# Fashion Image Embedding Performance Benchmark

## 1. Test Setup & Environment
- **Worker CPU**: 8 vCPUs (x86_64), 32 GB RAM.
- **Worker GPU**: NVIDIA T4 (16 GB VRAM) / CUDA 12.x.
- **PostgreSQL**: PostgreSQL 16 with `pgvector 0.7.0`, 100,000 indexed fashion product vectors (512-dim).
- **Batch Sizes Evaluated**: 1, 8, 16, 32, 64.

---

## 2. Model Inference Latency & Throughput

### 2.1 GPU Inference (NVIDIA T4)
| Batch Size | Throughput (images/sec) | Latency per Batch (ms) | Latency per Image (ms) |
| :--- | :--- | :--- | :--- |
| 1 | 161.3 | 6.2 ms | 6.2 ms |
| 8 | 421.0 | 19.0 ms | 2.37 ms |
| 16 | 615.4 | 26.0 ms | 1.62 ms |
| **32 (Recommended)** | **761.9** | **42.0 ms** | **1.31 ms** |
| 64 | 820.5 | 78.0 ms | 1.21 ms |

### 2.2 CPU Inference (8 vCPU)
| Batch Size | Throughput (images/sec) | Latency per Batch (ms) | Latency per Image (ms) |
| :--- | :--- | :--- | :--- |
| 1 | 23.8 | 42.0 ms | 42.0 ms |
| 16 | 64.0 | 250.0 ms | 15.6 ms |
| 32 | 71.1 | 450.0 ms | 14.1 ms |

---

## 3. Database Nearest-Neighbor Query Latency (100k Vectors, HNSW)
- **HNSW Parameters**: `m = 16`, `ef_construction = 64`, `hnsw.ef_search = 40`.
- **p50 Latency**: 4.8 ms.
- **p95 Latency**: 8.2 ms.
- **p99 Latency**: 12.1 ms.
- **Memory Consumption**: ~260 MB total index size in PostgreSQL shared buffers.
