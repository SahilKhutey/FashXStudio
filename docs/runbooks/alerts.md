# Operational Alerting Runbook

## Overview
This runbook defines alerting classifications, thresholds, dispatch channels, and triage steps for FashXStudio production environments hosted in AWS Mumbai (`ap-south-1`).

To prevent alert fatigue while safeguarding availability and compliance, alerts are strictly separated into **Paging Alerts** (wake on-call immediately, 24/7) and **Daily Digest / Warning Alerts** (business-hours notification in Slack `#eng-alerts` or email).

---

## 1. Paging Alerts (Critical / 24x7 On-Call)

| Alert Name | Condition & Window | Source Metric / Log Query | Triage & Immediate Action |
| :--- | :--- | :--- | :--- |
| `APIHigh5xxRate` | `5xx error rate > 2%` for 5 min | ALB / ECS CloudWatch Metric `HTTPCode_Target_5XX_Count` / `RequestCount` | Check CloudWatch logs for unhandled exceptions or database connection pool exhaustion. Check RDS CPU/connections. Trigger blue/green rollback if linked to recent deploy. |
| `FeedLatencyP95Critical` | `p95(GET /v1/feed) > 600ms` for 10 min | ALB Target Response Time or application log field `latency` on `/v1/feed` | Check pgvector query times and iterative HNSW scan execution. Verify Redis cache hit rates. Disable heavy ranking stages or activate graceful degradation feed fallback. |
| `TryOnFailureRateHigh` | `Failure rate > 15%` for 15 min OR `5 consecutive failed jobs` | Celery task error rate on `fashx.workers.tasks.tryon` or DB `tryon_jobs.status == 'failed'` | Check try-on provider status (FASHN / modal). Check credit balance or rate limits. If external provider down, activate try-on circuit breaker / kill switch (`tryon_enabled = False`) to show user-friendly maintenance banner. |
| `CeleryQueueBacklog` | `Queue depth > 100` for 10 min | Redis queue length (`LLEN celery`) or CloudWatch queue alarm | Check if worker containers died or are CPU-starved. Scale Celery worker Fargate tasks from 2 to 4+. Inspect slow/hung jobs. |
| `DatabaseDiskUsageHigh` | `Free storage space < 15%` (Disk > 85%) | RDS CloudWatch Metric `FreeStorageSpace` | Scale RDS storage allocation immediately (storage autoscaling trigger). Clean up old temp tables or vacuum orphaned indexes. |
| `DatabaseReplicaLag` | `Replication lag > 60s` for 3 min | RDS Metric `ReplicaLag` | Check replica IOPS and long-running analytics queries. Divert read traffic to primary if replica falls dangerously behind. |

---

## 2. Non-Paging Alerts (Daily Digest / Business Hours Warning)

| Alert Name | Condition | Channel | Remediation / Follow-up |
| :--- | :--- | :--- | :--- |
| `FeedLatencyP95Warning` | `p95(GET /v1/feed) > 350ms` for 15 min | Slack `#eng-alerts` | Performance regression investigation. Review recent catalog additions, MMR diversity stage compute, or vector search plan. |
| `ZeroTrafficAnomaly` | DAU or signups drops to 0 during peak hours (10:00 - 22:00 IST) | Slack `#eng-alerts` | Verify mobile app client builds, DNS resolution, and auth provider status. Check if an app store update caused client crashes. |
| `TryOnBudgetCapWarning` | External try-on vendor API spend > $50 in 24 hours | Slack `#eng-alerts` & Email to Founder | Inspect sudden usage surge. Check for abusive accounts or bot traffic. Verify per-user daily try-on rate limits (10/day). |
| `AbusiveIPBurst` | Single IP address making `> 500 req/min` | Slack `#security-alerts` | AWS WAF rate limit rule should automatically throttle to 429. Verify IP reputation; add manual IP block if malicious crawler. |
| `SSLCertificateExpiry` | ACM certificate expires in `< 30 days` | Slack `#eng-alerts` & Email | AWS ACM certificates auto-renew with DNS validation. If failing, verify Route 53 CNAME validation records. |
| `RetentionJobFailure` | Unsaved try-on images not deleted after 31 days | Slack `#eng-alerts` | Celery beat retention task failed. Inspect `backend/fashx/application/retention.py` worker logs. Run manual retention execution script. |

---

## 3. Escalation & Triage Protocol

1. **Acknowledge within 15 minutes** for all paging alerts in the incident tool.
2. **Post incident banner** to `#incident-prod` with incident commander (IC).
3. **Check `/healthz/ready`** and ECS task logs in AWS CloudWatch console.
4. If an unrecoverable failure is detected, follow [`break-glass.md`](./break-glass.md) or [`deploy-and-rollback.md`](./deploy-and-rollback.md).
