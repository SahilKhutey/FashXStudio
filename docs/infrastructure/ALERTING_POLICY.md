# Alerting Policy & CloudWatch Alarm Catalog

## 1. Alerting Philosophy

The FashXStudio alerting strategy prioritizes signal over noise to eliminate alert fatigue. Every triggered alarm must meet three criteria:
1. **User or Business Impact**: The condition affects real user requests, system data integrity, regulatory compliance, or infrastructure cost runaway.
2. **Actionability**: The alert references an explicit runbook with actionable diagnosis and remediation steps.
3. **Appropriate Urgency**: Triage severity matches the real-world operational consequence.

## 2. Severity Hierarchy & Response SLA

| Tier | Urgency | Notification Channel | Response SLA | Examples |
| :--- | :--- | :--- | :--- | :--- |
| **P1 — Critical** | Immediate threat to platform availability, data security, or third-party billing | SNS `fashx-alerts-prod` → Pager / SMS | < 15 minutes (24/7) | API 5xx spike, database storage exhaustion, VTO vendor 401 auth failure, dead-letter job accumulation, total worker outage. |
| **P2 — High** | Degraded performance, queue accumulation, or dependency throttling | SNS `fashx-alerts-prod` → High-priority email / chat | < 1 hour (business hours) | API p95 latency > 2000ms, VTO vendor 429 rate limits, RDS CPU > 80%, database pool saturation > 85%. |
| **P3 — Warning** | Proactive capacity warning or budget advisory | SNS `fashx-alerts-staging` / email | Next business day | AWS Budget at 80%, non-production queue buildup, transient retry spikes. |

## 3. Production CloudWatch Alarm Catalog

Alarms are declared in `infra/aws/observability/cloudwatch/alarms.yaml`:

```yaml
# Summary of declared production alarms
```

| Alarm Identifier | Namespace | Metric Name | Threshold | Evaluation | Tier |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `API-5xx-Rate-High-Production` | `FashX/API` | `Api5xxErrors` | > 10 errors | 2 of 2 mins | **P1** |
| `API-Latency-High-Production` | `FashX/API` | `ApiLatency` (p95) | > 2000 ms | 3 of 5 mins | **P2** |
| `RDS-CPU-High-Production` | `AWS/RDS` | `CPUUtilization` | > 85 % | 3 of 5 mins | **P2** |
| `RDS-Free-Storage-Low-Production` | `AWS/RDS` | `FreeStorageSpace` | < 5 GB | 1 of 1 min | **P1** |
| `DB-Connection-Pool-Exhaustion-Production` | `FashX/Database` | `DbPoolCheckedOut` | > 17 (85%) | 3 of 3 mins | **P2** |
| `Queue-Depth-High-Production` | `FashX/Queues` | `QueueDepth` (`vto`) | > 50 jobs | 3 of 5 mins | **P2** |
| `Dead-Letter-Queue-Non-Zero-Production` | `FashX/Queues` | `QueueDepth` (`dead_letter`) | > 0 jobs | 1 of 1 min | **P1** |
| `Worker-Heartbeat-Missing-Production` | `FashX/Workers` | `WorkerHeartbeat` | < 1 count | 3 of 3 mins | **P1** |
| `S3-Storage-Errors-Production` | `FashX/Storage` | `StorageUploadError` + `DeleteError` | > 5 errors | 2 of 5 mins | **P1** |
| `VTO-Provider-Rate-Limit-Production` | `FashX/VTO` | `VTOProviderRateLimit` | > 3 counts | 2 of 5 mins | **P2** |
| `VTO-Provider-Auth-Failure-Production` | `FashX/VTO` | `VTOProviderAuthFailure` | > 0 counts | 1 of 1 min | **P1** |
| `VTO-Failure-Rate-High-Production` | `FashX/VTO` | `VTOJobFailed` | > 5 failures| 2 of 5 mins | **P1** |

## 4. Notification Topics & Routing

Notification topics are declared in `infra/aws/observability/cloudwatch/sns-topics.yaml`:
- `arn:aws:sns:ap-south-1:<ACCOUNT_ID>:fashx-alerts-dev`: Low-priority testing and build notifications.
- `arn:aws:sns:ap-south-1:<ACCOUNT_ID>:fashx-alerts-staging`: Pre-release quality gate and deployment alerts.
- `arn:aws:sns:ap-south-1:<ACCOUNT_ID>:fashx-alerts-prod`: Production operational incident notifications.

## 5. Maintenance Windows & Silencing

To prevent alert storms during planned deployments or database maintenance:
1. Scheduled maintenance periods must be registered in the operations calendar.
2. CloudWatch Alarms can be muted via AWS CLI during maintenance tasks:
   ```bash
   aws cloudwatch disable-alarm-actions --alarm-names "API-5xx-Rate-High-Production"
   ```
3. Post-maintenance, alarm actions must be immediately re-enabled and smoke-tested:
   ```bash
   aws cloudwatch enable-alarm-actions --alarm-names "API-5xx-Rate-High-Production"
   ```
