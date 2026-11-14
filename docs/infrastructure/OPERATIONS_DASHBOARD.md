# Operations Dashboard Specification — Single Pane of Glass

## 1. Overview

The `FashXStudio-Production-Operations` dashboard is declared in `infra/aws/observability/cloudwatch/dashboard.json`. It provides the primary operational console for monitoring the health, performance, throughput, and error rates of all FashX services running in AWS Mumbai (`ap-south-1`).

The dashboard visualizes metrics emitted via CloudWatch Embedded Metric Format (EMF) alongside native AWS RDS, ElastiCache, and ECS telemetry.

## 2. Dashboard Layout & Widget Breakdown

The dashboard is structured into six functional operational panels:

```
+-------------------------------------------------------------------------------+
| 1. API GATEWAY HEALTH & LATENCY                                               |
| [ Request Throughput & Status Codes ]    [ API Latency Percentiles (p50/p95) ]|
+-------------------------------------------------------------------------------+
| 2. CELERY QUEUES & WORKER HEALTH                                              |
| [ Queue Depths (vto, catalog, dlq) ]     [ Worker Heartbeats & Task Rates ]   |
+-------------------------------------------------------------------------------+
| 3. DATABASE ENGINE & CONNECTION POOL                                          |
| [ RDS CPU & Freeable Memory ]            [ SQLAlchemy Connection Pool Usage ] |
+-------------------------------------------------------------------------------+
| 4. VTO INFERENCE PROVIDER (FASHN)                                             |
| [ Inference Success vs Failures ]        [ Rate Limits (429) & Provider SLA ] |
+-------------------------------------------------------------------------------+
| 5. S3 STORAGE OPERATIONS & PRIVACY                                            |
| [ S3 Upload/Download Throughput ]        [ Storage Operation Latency & Errors]|
+-------------------------------------------------------------------------------+
| 6. SYSTEM HEALTH & DEPENDENCY PROBES                                          |
| [ Live & Ready Endpoint Probes ]         [ Redis & DB Ping Round-Trip Latency]|
+-------------------------------------------------------------------------------+
```

### Panel 1: API Gateway Health & Latency
- **Request Volume**: Stacked bar/line chart displaying `ApiRequestsCount` segmented by `StatusCode` (2xx, 4xx, 5xx).
- **Latency Distribution**: Line chart tracking `ApiLatency` with percentile aggregations: `p50` (green), `p95` (orange), `p99` (red).

### Panel 2: Celery Queues & Worker Health
- **Queue Depths**: Multi-line graph tracking `QueueDepth` across `vto`, `catalog`, `default`, and `dead_letter`.
- **Worker Heartbeats**: Status widget showing active worker heartbeats emitted every 60 seconds (`WorkerHeartbeat`).
- **Task Lifecycle**: Throughput graph of `TaskStarted`, `TaskSucceeded`, `TaskRetried`, and `TaskFailed`.

### Panel 3: Database Engine & Connection Pool
- **RDS Performance**: Dual-axis graph of `AWS/RDS` `CPUUtilization` and `FreeStorageSpace`.
- **SQLAlchemy Pool Checkout**: Stacked area chart showing `DbPoolCheckedIn`, `DbPoolCheckedOut`, and `DbPoolOverflow` against max capacity.

### Panel 4: VTO Inference Provider (FASHN API)
- **Inference Reliability**: Time-series comparing `VTOJobSubmitted` vs `VTOJobSucceeded` vs `VTOJobFailed`.
- **Upstream Errors**: Bar chart isolating `VTOProviderRateLimit` (429), `VTOProviderAuthFailure` (401), and `VTOProviderTimeout`.
- **Cumulative Estimated Spend**: Running metric math summation of `VTOProviderCostEstimate`.

### Panel 5: S3 Storage Operations & Privacy
- **Storage Operations**: Time-series tracking `StorageUploadCount`, `StorageDownloadCount`, and `StorageDeleteCount`.
- **Erasure Compliance**: Alert counter for `StorageDeleteError` (must be zero).

### Panel 6: System Health & Dependency Probes
- **Readiness Status**: Gauge reflecting `/healthz/ready` probe outcomes.
- **Dependency Round-Trip Latency**: Dual-line graph comparing `DbCheckLatency` (ms) and `RedisPingLatency` (ms).

## 3. Incident Triaging with CloudWatch Logs Insights

When a dashboard graph displays an anomaly (e.g. latency spike or 5xx surge), operators can pivot directly to CloudWatch Logs Insights using saved queries:

### Query: Top 5xx Errors by Route
```sql
fields @timestamp, route, status_code, message, request_id, trace_id
| filter status_code >= 500
| stats count(*) as error_count by route, message
| sort error_count desc
| limit 20
```

### Query: Slow Requests Exceeding 1000ms
```sql
fields @timestamp, route, duration_ms, status_code, request_id
| filter duration_ms > 1000
| sort duration_ms desc
| limit 25
```
