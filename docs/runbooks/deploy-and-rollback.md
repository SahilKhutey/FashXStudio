# Deployment & Rollback Runbook

## 1. Overview & Architecture

FashXStudio deploys to AWS ECS Fargate via GitHub Actions (`.github/workflows/deploy.yml`) using OIDC authentication and rolling task replacements.

- **Zero-Downtime Guarantee**: ECS maintains minimum healthy percent at 100% and maximum percent at 200%. New tasks must pass `/healthz/ready` target group checks before old tasks are drained.
- **Fail-Safe Target Group**: Target group probes `/healthz/ready` every 15s (healthy threshold: 2, unhealthy: 3, timeout: 5s).

---

## 2. Standard Deployment Procedure

1. **Verify Staging Checks**:
   - All 1,150+ tests pass in CI.
   - Trivy container security scan passes with zero HIGH/CRITICAL vulnerabilities.
2. **Execute Database Migrations**:
   - Run Alembic migrations:
     ```bash
     alembic upgrade head
     ```
3. **Deploy ECS Task Definition**:
   - Register new task definition revision in AWS ECS.
   - Update ECS service `fashx-api`:
     ```bash
     aws ecs update-service --cluster fashx-prod --service fashx-api --task-definition fashx-api:NEW_REV --force-new-deployment
     ```
4. **Run Smoke Tests**:
   - Execute `scripts/release/smoke.py --base https://api.fashx.studio` to verify `/api/v1/system/health/ready`, `/api/v1/config`, and core routes.

---

## 3. Fast Rollback Procedure (Emergency Triage)

When a deployment introduces errors or breaks `/healthz/ready`:

### Step 1: Rollback ECS Service Immediately
Revert to the previous known good task definition revision (takes < 2 minutes):
```bash
aws ecs update-service \
  --cluster fashx-prod \
  --service fashx-api \
  --task-definition fashx-api:PREVIOUS_STABLE_REV \
  --force-new-deployment
```

### Step 2: Verify Rollback Health
```bash
aws ecs wait services-stable --cluster fashx-prod --services fashx-api
python scripts/release/smoke.py --base https://api.fashx.studio
```

---

## 4. Database Migration Safety: Expand-Contract Pattern

Database migrations must never cause downtime when rolling back ECS tasks. Always use the **Expand-Contract (Parallel Run) Pattern**:

1. **Phase 1 (Expand)**: Add new columns as nullable, add new tables, or add additive indexes.
   - Code running old task revision can safely ignore the new columns.
   - Code running new task revision begins writing to both old and new columns.
2. **Phase 2 (Migrate Data)**: Backfill data in the background if necessary.
3. **Phase 3 (Contract)**: After the new code version has run stably in production for at least 7 days:
   - Deploy subsequent migration to drop deprecated columns or tables.
   - **Rule**: Never drop a column or rename a table in the same release that first stops using it.
