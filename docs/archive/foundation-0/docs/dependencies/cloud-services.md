# Dependency Register: Cloud Services & Storage Infrastructure

| Service | Provider | Purpose | SLA Target | Local Dev Substitute |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Relational DB** | PostgreSQL 16 + `pgvector` | Authoritative entity storage & vector search | 99.95% | Local Docker Compose `pgvector/pgvector:pg16` |
| **Cache & Task Broker** | Redis 7.2 | Rate limits, ephemeral capability tokens, queue | 99.99% | Local Docker Compose `redis:7.2-alpine` |
| **Object Storage** | Cloudflare R2 / AWS S3 | Encrypted user portraits, garment masks, renders | 99.9% | Local MinIO / Filesystem Adapter |
| **GPU Inference Pool** | Modal / RunPod / AWS EC2 G5 | Diffusion VTO rendering & VLM attribute extraction | On-demand / Burst | Mock local inference provider |
| **Error Monitoring** | Sentry SDK (FastAPI) | Production exception tracking & trace correlation | Best Effort | Console JSON structured log |

---

## 1. Storage & Capability Token Security

- User portraits stored in R2/S3 are private by default (no public read permissions).
- All downloads are governed by presigned URLs expiring within 900 seconds.
