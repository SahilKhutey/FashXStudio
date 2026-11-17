# Rollback Runbook and Emergency Operating Procedures

## 1. Rollback Criteria

A production or staging rollback must be initiated immediately if:
1. HTTP 5xx error rate exceeds 1% over a 3-minute sliding window.
2. API P95 latency exceeds 2,000ms for 5 consecutive minutes.
3. Health check probes (`/healthz/live` or `/healthz/ready`) fail.
4. Post-deployment smoke test (`scripts/release/smoke.py`) fails.
5. Critical application regression or database deadlock occurs.

## 2. Automated Rollback in CI/CD Pipeline

Both `deploy-staging.yml` and `deploy-production.yml` implement automated rollback hooks:

```yaml
- name: Automatic Rollback on Failure
  if: failure() && steps.check-deploy-role.outputs.configured == 'true'
  run: |
    bash scripts/release/rollback_ecs.sh <staging|prod> /tmp/deploy-state/rollback_state.json
```

1. **State Capture**: Before updating any ECS service, the deployment workflow captures the active task definition ARN for each service into `/tmp/deploy-state/rollback_state.json`.
2. **Circuit Breaker**: ECS deployment circuit breakers automatically detect task restart crashes and initiate ECS-level rollback.
3. **Pipeline Rollback Script**: If smoke testing fails after ECS reports stability, `scripts/release/rollback_ecs.sh` forces immediate reversion to the pre-deployment task definitions.

## 3. Manual Operator Rollback (Emergency CLI)

If the pipeline is inaccessible, operators can trigger emergency rollback using `scripts/release/rollback_ecs.sh`:

```bash
# 1. Assume Deployment Role
aws-vault exec fashx-deploy -- bash

# 2. Execute rollback for target environment
bash scripts/release/rollback_ecs.sh prod

# 3. Verify stabilization and run smoke test
python scripts/release/smoke.py --base "https://api.fashxstudio.com"
```

## 4. Database Migration Rollback

If a database migration introduced an incompatible schema:
- If the change was backward-compatible (Expand phase), application services can roll back to the prior version immediately without rolling back the database.
- If a schema downgrade is strictly required:
  ```bash
  python -m alembic downgrade -1
  ```
- If data corruption occurred, restore the RDS instance from the point-in-time WAL archive to the minute immediately preceding the release.
