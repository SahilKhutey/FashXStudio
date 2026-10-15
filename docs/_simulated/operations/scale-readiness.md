# Scale Readiness & Technical Architecture for Phase 13

- **Version:** 1.0 (Post-Gate 2 Scale Readiness)
- **Target Scale:** 50+ Partner Brands, 250,000+ Try-On Generations / Month

---

## 1. Inference Engine & GPU Worker Autoscaling

To support 10x traffic growth while preserving unit costs ($\le ₹1.20$ / generation), the inference worker architecture transitions from static capacity to an event-driven worker pool.

```
[Shopper Try-On Request] 
          ↓
[FastAPI Backend: /widget/v1/tryon] 
          ↓
[Redis Celery Queue (Try-On Jobs)]
          ↓
[KEDA / HPA Queue Monitor] ─── Queue Depth > 15 ───→ [Scale GPU Worker Nodes]
          ↓
[GPU Worker Pool: NVIDIA A10G / L4]
  - Quantized FP8 / INT8 Weights
  - Batch size: 4 concurrent jobs
  - In-flight inference latency: p50 6.2s, p95 9.8s
```

### Scaling Rules & Triggers
- **Scale-Up Threshold:** If Redis queue depth $> 15$ jobs for $> 45$ seconds, spawn $+2$ worker pods. Max ceiling: 16 pods.
- **Scale-Down Threshold:** If queue depth $= 0$ for $> 10$ consecutive minutes, terminate idle worker pods. Maintain 1 warm spot instance.
- **Multi-Cloud GPU Fallback:** Primary: AWS G5.xlarge Spot instances (Mumbai `ap-south-1`). Secondary failover: RunPod / Lambda Labs secure Indian endpoints.

---

## 2. Database Topology & Query Segregation

```
                 [Write Traffic (API)]
                          ↓
              [PostgreSQL Primary (RDS)]
                     /          \
   (Streaming Replication)  (Streaming Replication)
                   /              \
       [Read Replica 1]         [Read Replica 2]
              ↓                        ↓
  [Widget Session Queries]    [Merchant Analytics & Dashboards]
```

- **PgBouncer Pooling:** Transaction-level connection pooling enabled; caps backend connections at 100 per instance, preventing connection starvation during PDP traffic spikes.
- **Read Segregation:** All heavy dashboard queries (`/merchant/dashboard`, `v_tenant_usage`, `v_events`) route to Read Replica 2.

---

## 3. Edge CDN & Widget Delivery Architecture

- **Asset Hosting:** S3 origin behind Cloudflare Enterprise CDN.
- **Wire Size:** The uncompressed script is 32KB; Brotli compressed payload size is **11.4KB**.
- **Edge Cache Headers:**
  ```http
  Cache-Control: public, max-age=3600, stale-while-revalidate=86400
  Content-Encoding: br
  ```
- **Instant Invalidation Pipeline:** When new versions are tagged, GitHub Actions triggers Cloudflare API cache purge in $< 3$ seconds.

---

## 4. Disaster Recovery & Failover SLAs

- **Recovery Point Objective (RPO):** $< 5\text{ minutes}$ (Automated continuous WAL archiving to multi-region S3).
- **Recovery Time Objective (RTO):** $< 15\text{ minutes}$ (Infrastructure as Code via Terraform / Helm charts).
- **Graceful Widget Fallback:** If API enters 5xx state, widget automatically falls back to static brand size chart modal without breaking host PDP functionality.
