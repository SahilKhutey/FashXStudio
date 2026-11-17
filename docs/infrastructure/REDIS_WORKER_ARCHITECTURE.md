# Redis Broker & Background Worker Architecture Specification

## 1. Executive Summary

FashXStudio deploys Amazon ElastiCache for Valkey (Redis 7.2 compatible) as the asynchronous task queue broker in AWS Mumbai (`ap-south-1`), paired with distributed Celery workers running on Amazon ECS Fargate.

The architecture isolates queue brokers by environment and provisions three specialized worker services alongside a singleton scheduler.

```mermaid
flowchart TD
    API[FastAPI Gateway] -->|apply_async / W3C Trace Context| Redis[(Amazon ElastiCache Valkey/Redis)]
    
    subgraph CeleryQueues [Task Queues (maxmemory-policy=noeviction)]
        Q1[tryon Queue]
        Q2[ingest Queue]
        Q3[maintenance Queue]
    end

    Redis --> Q1
    Redis --> Q2
    Redis --> Q3

    Q1 --> WorkerTryon[ECS Service: fashx-staging-tryon]
    Q2 --> WorkerIngest[ECS Service: fashx-staging-ingest]
    Q3 --> WorkerMaint[ECS Service: fashx-staging-maintenance]
    
    Beat[ECS Service: fashx-staging-beat<br/>Singleton Scheduler] -->|Periodic Tasks| Q3
    
    WorkerTryon --> DLQ[Dead Letter Table / CloudWatch Alert]
    WorkerIngest --> DLQ
    WorkerMaint --> DLQ
```

## 2. Broker Provisioning & Configuration

| Parameter | Configuration | Operational Purpose |
| :--- | :--- | :--- |
| **Engine** | Valkey / Redis 7.2 | High-throughput asynchronous broker. |
| **Transit Encryption** | `true` (`rediss://`) | Encrypts all in-flight payloads across VPC subnets. |
| **At-Rest Encryption** | `true` (KMS) | Protects persistence snapshots and swap. |
| **Authentication** | Random 32-char token | Strong token-based authentication via Secrets Manager. |
| **`maxmemory-policy`** | `noeviction` | **Mandatory**: Prevents silent eviction of queued tasks. |
| **Timeout** | 300 seconds | Closes idle worker connections. |

## 3. Queue Topology & Worker Specialization

1. **`tryon` Queue**:
   - Consumer: `fashx-<env>-tryon` ECS Service.
   - Workload: Upstream VTO API dispatch (FASHN), status polling, image compositing, and result persistence.
   - Sizing: Scaled based on queue depth metrics (`QueueDepth > 50`).
2. **`ingest` Queue**:
   - Consumer: `fashx-<env>-ingest` ECS Service.
   - Workload: Merchant product catalog feed processing, image background removal, and vector embeddings calculation.
3. **`maintenance` Queue**:
   - Consumer: `fashx-<env>-maintenance` ECS Service.
   - Workload: Outbox event relaying, user media erasure sweeps (GDPR/DPDP), and soft retention cleanup.
4. **`beat` Scheduler**:
   - Consumer: `fashx-<env>-beat` ECS Service.
   - Topology: Singleton task (desired count = 1). Schedules outbox relays (every 30s) and retention sweeps (every 5m).

## 4. Reliability & Fault-Tolerance Controls

- **Late Acknowledgement (`task_acks_late = True`)**: Tasks are acknowledged only after worker execution completes. If a worker task terminates mid-flight, the job remains unacknowledged in Redis for redelivery.
- **Worker Crash Recovery (`task_reject_on_worker_lost = True`)**: Tasks lost due to container OOM killer or host termination are immediately rejected and rescheduled.
- **Soft Shutdown Timeout (`worker_soft_shutdown_timeout = 90.0`)**: During rolling deployments or task termination, workers stop receiving new tasks and finish in-flight work within 90 seconds before container exit.
- **Dead-Letter Handling**: Tasks exceeding maximum retries trigger dead-letter callbacks (`persist_dead_letter_sync`) storing sanitized error types and metadata without logging customer media or PII.
- **Worker Heartbeat Telemetry**: Workers emit periodic `WorkerHeartbeat` metrics to CloudWatch (`FashX/Workers`) every 60 seconds.
