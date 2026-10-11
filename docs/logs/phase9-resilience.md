# Resilience & Failure Injection Scorecard (Phase 9)

**Date**: 2026-10-11  
**Environment**: Staging (`ap-south-1`)  
**Tools**: k6 (`scripts/perf/k6_feed_load.js`), Chaos testing harness, Redis CLI, Toxiproxy  

---

## 1. Load Testing Scorecard (`GET /api/v1/feed`)

The k6 benchmark was executed against the production container topology with 100 virtual users (VUs) ramping over 2.5 minutes at 50 requests/second.

| Metric | Target SLA | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **P50 Latency** | < 100ms | **18.4ms** | **PASSED** |
| **P95 Latency** | < 350ms | **42.1ms** | **PASSED** |
| **P99 Latency** | < 600ms | **88.6ms** | **PASSED** |
| **Max Latency** | < 1,500ms | **184.2ms** | **PASSED** |
| **Throughput** | 50.0 req/sec | **52.4 req/sec** | **PASSED** |
| **Error Rate (5xx)** | < 1.0% | **0.00% (0 / 7,850 requests)** | **PASSED** |
| **Database CPU** | < 70% | **18.5% peak** | **PASSED** |

---

## 2. Failure Injection Scenarios & Graceful Degradation Matrix

| Failure Injected | Injection Method | Expected Behavior | Actual Observed System Response | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DB Connection Pool Saturation** | Injected 200 concurrent requests against a pool cap of 50. | SQLAlchemy connection pool queues requests up to `pool_timeout=30s`. Clean 503 on timeout; zero process crashes. | Requests queued cleanly. 96% served within timeout. 4% received graceful `503 Service Unavailable` with `Retry-After`. Uvicorn process stayed healthy. | **PASSED** |
| **Redis Outage** | Stopped Redis service (`docker stop redis`). | Application survives. Rate limiter fails open (logs warning, avoids user lockout). Feed serves unranked fallback. `/healthz/ready` flags Redis degraded. | Rate limiter logged warning and allowed traffic. Cache hit fell back to direct DB queries. `/healthz/ready` returned 503 indicating `{"redis": "degraded"}`. | **PASSED** |
| **Try-On Provider Upstream 504 Timeout** | Injected 65-second latency into external try-on mock via Toxiproxy. | Celery worker times out after 60s, records failed job, circuit breaker records failure. | Job marked `failed` with `reason="PROVIDER_TIMEOUT"`. After 5 consecutive failures, circuit breaker tripped to OPEN, rejecting subsequent requests early in 2ms. | **PASSED** |
| **S3 Throttling (503 Slow Down)** | Injected transient 503 responses on 25% of S3 PUT calls. | Client and worker SDK retries with exponential jittered backoff. | Botocore retry handler executed 3 retries with full jitter; 100% of uploads succeeded without user-visible errors. | **PASSED** |
| **Dynamic Kill Switch (`tryon_enabled=False`)** | Sent admin API flag toggle. | Try-on requests immediately rejected with 503 within 30 seconds across all nodes. | Within < 1 second, all tryon job submissions returned `503 Service Unavailable` with `TRYON_TEMPORARILY_DISABLED`. Feed & wardrobe remained 100% responsive. | **PASSED** |

---

## 3. Resilience Conclusions

1. **Failure Containment**: Non-critical dependency outages (Redis, external try-on vendor) never bring down core container processes or cause cascading crashes.
2. **Predictable Latency**: Feed query latency under full 100-user concurrency remains well within the 350ms SLA, leveraging indexed filter columns and in-memory caches.
3. **Pilot Readiness**: The architecture meets all resilience requirements for the closed 100-user invite pilot.
