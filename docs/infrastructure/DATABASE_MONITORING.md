# Database Monitoring & Connection Pool Telemetry

## 1. Overview

FashXStudio operates on isolated Amazon RDS PostgreSQL 16 instances in AWS Mumbai (`ap-south-1`). Database observability combines:
1. **AWS RDS CloudWatch Infrastructure Metrics**: Managed database engine telemetry (CPU, disk, memory, IOPS).
2. **Application-Level SQLAlchemy Pool Telemetry**: Real-time connection checkout, saturation, and latency monitoring implemented in `backend/fashx/core/database.py`.

## 2. Infrastructure Metrics (Amazon RDS)

AWS RDS automatically publishes telemetry to the `AWS/RDS` CloudWatch namespace under dimension `DBInstanceIdentifier`:

| Metric Name | Threshold | Description |
| :--- | :--- | :--- |
| `CPUUtilization` | Warning: > 70%<br>Critical: > 85% | Percentage of CPU utilized by the PostgreSQL engine. |
| `FreeStorageSpace` | Warning: < 10 GB<br>Critical: < 5 GB | Remaining disk storage on the RDS EBS volume. |
| `FreeableMemory` | Warning: < 256 MB | RAM available for database caching and query execution. |
| `DatabaseConnections` | > 80% of max allowed | Number of active PostgreSQL backend worker processes. |
| `ReadLatency` / `WriteLatency` | > 20 ms average | Average storage read/write operation latency. |

## 3. Application-Level Pool Telemetry (SQLAlchemy)

To catch connection leaks, pool starvation, and runaway transactions before RDS is overwhelmed, `backend/fashx/core/database.py` instruments the SQLAlchemy `QueuePool`:

```python
from fashx.core.database import get_db_pool_metrics, emit_db_pool_metrics

# Retrieve raw status
metrics = get_db_pool_metrics(engine)
# Emits CloudWatch EMF record to namespace 'FashX/Database'
emit_db_pool_metrics(engine, environment="prod")
```

### Emitted EMF Metrics (`FashX/Database`)

| Metric Name | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `DbPoolSize` | Gauge | Count | Maximum persistent pool size configured (`settings.db_pool_size`). |
| `DbPoolCheckedIn` | Gauge | Count | Connections currently idle and available in the pool. |
| `DbPoolCheckedOut` | Gauge | Count | Connections actively checked out by executing requests. |
| `DbPoolOverflow` | Gauge | Count | Temporary connections opened above the persistent pool size. |
| `DbCheckLatency` | Timer | Milliseconds | Latency of the health check query (`SELECT 1`). |
| `DbConnectionError` | Counter | Count | Count of database connection acquisition failures. |

### Pool Dimensions
- `Environment`: `dev`, `staging`, `prod`

## 4. Connection Exhaustion Alarms

CloudWatch Alarm `DB-Connection-Pool-Exhaustion-Production` monitors `DbPoolCheckedOut` against configured maximum limits:
- If `DbPoolCheckedOut + DbPoolOverflow >= (DbPoolSize + DbPoolMaxOverflow) * 0.85` for 3 consecutive minutes, an alert is dispatched via SNS.
- On-call engineers inspect slow queries, long-running transactions, and Celery task hold times as detailed in the incident runbook.
