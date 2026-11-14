# Redis & Celery Queue Monitoring Specification

## 1. Overview

FashXStudio utilizes Amazon ElastiCache for Valkey (Redis-compatible) as the asynchronous task queue broker for Celery background tasks in AWS Mumbai (`ap-south-1`).

Monitoring covers both:
1. **ElastiCache Cluster Health**: CPU, memory utilization, connection counts, and evictions.
2. **Celery Queue Depth & Backlog**: Task accumulation per queue emitted via `backend/fashx/workers/telemetry.py` and health check latency in `backend/fashx/health/router.py`.

## 2. ElastiCache Infrastructure Metrics

Amazon ElastiCache publishes node metrics to CloudWatch under the `AWS/ElastiCache` namespace:

| Metric Name | Threshold | Description |
| :--- | :--- | :--- |
| `EngineCPUUtilization` | > 75% | CPU utilization of the single-threaded Redis engine. |
| `DatabaseMemoryUsagePercentage`| > 80% | Percentage of available memory consumed by Redis data structures. |
| `CurrConnections` | > 1000 | Active client connections (API instances + Celery workers). |
| `Evictions` | **Must be 0** | Keys evicted due to memory limits. In Celery brokers, evictions cause lost jobs. |
| `NetworkBytesIn` / `Out` | Baseline check | Inbound and outbound throughput. |

> [!CRITICAL]
> The `Evictions` metric must strictly remain 0. If Redis begins evicting queue lists due to memory exhaustion, background VTO jobs and catalog indexing tasks will be dropped silently.

## 3. Celery Queue Depth Telemetry

Task accumulation indicates worker starvation, slow upstream dependencies, or worker crashes.

`backend/fashx/workers/telemetry.py` periodically inspects queue lengths in Redis using `LLEN <queue_name>` and emits CloudWatch EMF records:

```python
from fashx.workers.telemetry import emit_queue_depth

# Emits EMF metric 'QueueDepth' to namespace 'FashX/Queues'
emit_queue_depth(
    broker_url=settings.redis_url,
    queue_name="vto",
    environment=settings.env,
)
```

### Monitored Queues
- `vto`: Virtual try-on inference dispatch, status polling, and image compositing.
- `catalog`: Product image ingestion, vector embedding generation, and indexing.
- `default`: General asynchronous operations, emails, and maintenance cleanup.
- `dead_letter`: Failed tasks that exhausted maximum retries.

### Emitted EMF Metrics (`FashX/Queues`)

| Metric Name | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `QueueDepth` | Gauge | Count | Number of pending messages waiting in the specified queue. |
| `RedisPingLatency` | Timer | Milliseconds | Latency of `PING` round-trip recorded during health checks. |
| `RedisConnectionError`| Counter | Count | Redis connection failures observed by API or workers. |

### Allowed Dimensions
- `Environment`: `dev`, `staging`, `prod`
- `QueueName`: `vto`, `catalog`, `default`, `dead_letter`

## 4. Queue Alarms & Escalations

1. **`Queue-Depth-High-Production`**:
   - Condition: `QueueDepth >= 50` on queue `vto` for 3 consecutive evaluation periods (5 minutes).
   - Action: P1 alert to SNS topic `fashx-alerts-prod`. Indicates need to scale worker concurrency or investigate upstream API latency.
2. **`Dead-Letter-Queue-Non-Zero-Production`**:
   - Condition: `QueueDepth > 0` on queue `dead_letter` for 1 period.
   - Action: P1 alert to SNS topic `fashx-alerts-prod`. Requires immediate triage of permanently failed tasks.
