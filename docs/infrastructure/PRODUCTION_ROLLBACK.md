# Production Rollback Runbook and Emergency Procedures

## 1. Rollback Trigger Criteria

A production rollback is immediately mandatory if any of the following operational thresholds are breached within 30 minutes of a deployment:

| Metric / Symptom | Trigger Condition | Detection Source |
| :--- | :--- | :--- |
| **HTTP 5xx Error Rate** | > 1.0% of total requests over 3 minutes | CloudWatch / ALB Metrics |
| **API Latency Degradation** | P95 latency > 2,000ms for 5 consecutive minutes | CloudWatch / Datadog |
| **Try-On Inference Failure** | VTO task failure rate > 15.0% over 10 minutes | Sentry / Celery Task Metrics |
| **Database Connectivity** | Connection pool exhaustion or deadlocks | RDS CloudWatch Alarms |
| **Health Check Failure** | `/healthz` returning 503 across > 25% of tasks | ALB Target Group Health |

---

## 2. Immediate Incident Mitigation: Feature Kill Switches

Before initiating an infrastructure rollback, engineers may immediately mitigate user impact using remote feature flags without waiting for task redeployment:

```bash
# 1. Disable Virtual Try-On if inference provider is degraded
aws ssm put-parameter \
  --name "/fashx/prod/TRYON_ENABLED" \
  --value "false" \
  --type "String" \
  --overwrite

# 2. Enable Maintenance Mode for severe database corruption or catastrophic outage
aws ssm put-parameter \
  --name "/fashx/prod/MAINTENANCE_MODE" \
  --value "true" \
  --type "String" \
  --overwrite
```

---

## 3. Container Rollback Procedure

Because container tasks are immutable and previous image tags remain present in Amazon ECR, rolling back to the known stable release candidate takes less than 5 minutes:

### Step 1: Identify Known Stable Tag
Retrieve the previous successful deployment Git SHA from the release ledger or GitHub Actions deployment log:
```bash
STABLE_TAG="<PREVIOUS_GIT_SHA>"
```

### Step 2: Roll Back ECS Service Tasks
Trigger an immediate update of the ECS services targeting the stable tag:
```bash
for SERVICE in fashx-api fashx-tryon fashx-ingest fashx-beat; do
  aws ecs update-service \
    --cluster fashx-production \
    --service "$SERVICE" \
    --task-definition "${SERVICE}:${STABLE_TAG}" \
    --force-new-deployment
done
```

### Step 3: Wait for Service Stabilization
```bash
aws ecs wait services-stable \
  --cluster fashx-production \
  --services fashx-api fashx-tryon fashx-ingest fashx-beat
```

### Step 4: Execute Post-Rollback Smoke Test
```bash
python scripts/release/smoke.py \
  --base "https://api.fashxstudio.com" \
  --token "$EMERGENCY_SMOKE_TOKEN"
```

---

## 4. Database Rollback Protocol

Under the **Expand and Contract** schema design, application code from release $N-1$ is fully backward-compatible with database schema changes made in release $N$.
- **Normal Rollback**: Do **not** execute `alembic downgrade -1` immediately. Revert the application container tasks first. Old application code continues to operate with the expanded schema.
- **Contract Migration Reversal**: If a migration broke existing table constraints, execute `alembic downgrade -1` exclusively via the isolated migration task definition:
  ```bash
  aws ecs run-task \
    --cluster fashx-production \
    --task-definition fashx-migration-task \
    --overrides '{"containerOverrides": [{"name": "migration", "command": ["python", "-m", "alembic", "downgrade", "-1"]}]}'
  ```

---

## 5. Recovery Objectives (RTO / RPO)

- **Recovery Time Objective (RTO)**:
  - Feature Flag Mitigation: < 2 minutes
  - Container Image Rollback: < 10 minutes
  - Full Cluster Reconstruction: < 45 minutes
- **Recovery Point Objective (RPO)**:
  - Database Transactions: < 5 minutes (guaranteed by continuous WAL archiving)
  - Object Storage Media: 0 data loss (guaranteed by S3 bucket versioning)
