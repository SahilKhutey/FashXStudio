# Amazon ECS Deployment Strategy Specification

## 1. Workload Topography

FashXStudio deploys on Amazon ECS Fargate across isolated clusters:
- Staging Cluster: `fashx-staging`
- Production Cluster: `fashx-prod`

### Services per Cluster:
1. **`fashx-<env>-api`**:
   - Runtime: FastAPI running on Gunicorn with Uvicorn workers (`gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000`).
   - Scaling: Minimum healthy percent 100%, Maximum percent 200%.
   - Ingress: AWS Application Load Balancer (ALB) with TLS termination.
2. **`fashx-<env>-tryon`**:
   - Runtime: Celery worker subscribed to queue `tryon` (`celery -A fashx.workers.app:app worker -Q tryon -c 2`).
   - Stop Timeout: 120 seconds (`stopTimeout: 120`) to allow ongoing VTO inference tasks to finish.
3. **`fashx-<env>-ingest`**:
   - Runtime: Celery worker subscribed to queue `ingest` (`celery -A fashx.workers.app:app worker -Q ingest -c 1`).
   - Stop Timeout: 120 seconds.
4. **`fashx-<env>-beat`**:
   - Runtime: Celery Beat scheduler (`celery -A fashx.workers.app:app beat`).
   - Scaling: Desired count 1 (singleton scheduler to prevent duplicate cron dispatch).
5. **`fashx-<env>-migration`**:
   - Ephemeral standalone Fargate task executed via `aws ecs run-task` prior to service updates.

## 2. Rolling Update Mechanics

Deployments use ECS rolling updates with zero downtime:

```bash
aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$SERVICE" \
  --task-definition "$TASK_DEF_ARN" \
  --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true},minimumHealthyPercent=100,maximumPercent=200"
```

### Invariants:
- **Minimum Healthy Percent (100%)**: Guarantees that at least the current capacity remains operational while new tasks start.
- **Maximum Percent (200%)**: Allows ECS to spin up a full set of new tasks alongside old tasks.
- **Deployment Circuit Breaker**: If new tasks fail health checks or exit repeatedly, ECS automatically stops the deployment and rolls back to the previous active task definition revision without operator intervention.
