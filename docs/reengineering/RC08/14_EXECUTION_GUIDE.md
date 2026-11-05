# RC08 — Execution Guide

## 1. Local Staging Rehearsal
To test the staging configuration locally:

```bash
# 1. Prepare environment configuration
cp .env.example .env

# 2. Spin up PostgreSQL 16 + pgvector and Redis
docker compose up -d postgres redis
docker compose ps

# 3. Apply database migrations
python -m alembic upgrade head
python -m alembic check

# 4. Run local regression test suite
python -m pytest tests -q -p no:cacheprovider -m "not frozen"

# 5. Start FastAPI application
python -m uvicorn fashx.main:app --host 0.0.0.0 --port 8000

# 6. Verify health probes
curl -s http://127.0.0.1:8000/healthz/live | jq .
curl -s http://127.0.0.1:8000/healthz/ready | jq .
```

## 2. Staging Deployment Execution
```bash
# 1. Build and tag container image
docker build -t fashx-backend:$(git rev-parse --short HEAD) -f Dockerfile .

# 2. Push to private registry
docker tag fashx-backend:$(git rev-parse --short HEAD) $REGISTRY_URL/fashx-backend:$(git rev-parse --short HEAD)
docker push $REGISTRY_URL/fashx-backend:$(git rev-parse --short HEAD)

# 3. Deploy and execute migration task in ECS
aws ecs run-task --cluster fashx-staging --task-definition fashx-migrate ...

# 4. Probe staging readiness endpoint
curl -f https://staging-api.fashx.com/healthz/ready
```

## 3. Rollback Runbook
If `/healthz/ready` returns 503 or error rate spikes post-deployment:
1. Re-point ECS service to previous image tag: `PREV_TAG=$(git rev-parse --short HEAD~1)`.
2. Do not run destructive schema downgrades if backwards-compatible column additions were used.
3. Drain unhealthy containers.
4. Verify `/healthz/ready` returns 200 OK.
