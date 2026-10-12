# Production Release Runbook & Staged Rollout Policy

- **Version:** 1.0
- **Scope:** Backend services, worker queues, DB migrations, CDN assets (`fashx-widget.js`)
- **Review Date:** Phase 12

---

## 1. Principles

1. **Zero Downtime:** All database migrations must follow the expand-contract pattern (never drop/rename columns in the same release as application code changes).
2. **Deterministic Promotion:** Every release artifact is built once in CI, tested against staging, and promoted via semantic git tags (`vX.Y.Z`).
3. **Canary Phasing:** Traffic shifts progressively with automated health checks and error rate gating.
4. **Instant Rollback:** Rollback must take $< 90$ seconds without requiring data restore.

---

## 2. Release Stages & Phasing

```
[Main Branch Merged] 
        ↓
[CI: Test Suite + Security Audit Pass] 
        ↓
[Tag Promotion: vX.Y.Z] 
        ↓
[Database Migrations Applied (Expand Phase)]
        ↓
[Canary Deployment: 5% Traffic (15 min observation)]
        ↓
[Phase 2: 25% Traffic (30 min observation)]
        ↓
[Phase 3: 100% Full Rollout]
        ↓
[Post-Deployment Smoke Tests & Error Budget Check]
```

---

## 3. Pre-Release Checklist

- [ ] All tests passing (`pytest -m "not frozen"`, Jest frontend suites).
- [ ] No unclassified tables in `backend/fashx/application/erasure.py`.
- [ ] Database migration backwards compatibility verified (`alembic upgrade head` compatible with old app version).
- [ ] Cloud CDN bundle size for `fashx-widget.js` verified $< 45\text{KB}$ uncompressed.
- [ ] Error budgets are in **Green** or **Yellow** state (releases blocked in **Orange/Red** per `slo.md`).
- [ ] On-call engineer confirmed active and monitoring dashboards.

---

## 4. Rollout Protocol

### Step 1: Tag & CI Build
```powershell
git checkout main
git pull origin main
git tag -a v1.1.0 -m "Release v1.1.0: B2B Multi-tenant platform"
git push origin v1.1.0
```

### Step 2: Database Migration (Expand)
Run alembic migration against production cluster:
```powershell
alembic upgrade head
```
*Verify: Zero table locks, replication lag remains $< 50\text{ms}$.*

### Step 3: Canary Deploy (5%)
- Route 5% of external tenant traffic to new pods.
- Monitor for 15 minutes:
  - Error rate must remain $< 0.05\%$.
  - p95 latency must remain $< 150\text{ms}$.
  - Worker exception count $= 0$.

### Step 4: Ramp to 25% and 100%
- If canary metrics hold green, advance to 25% for 30 minutes.
- If stable, shift 100% traffic to release containers.

---

## 5. Automated Rollback Triggers

Initiate immediate automated rollback (`helm rollback` / container revert) if any of the following occur during rollout:
1. **5xx Error Rate:** Exceeds 0.2% over any 3-minute window.
2. **P95 Latency Spike:** Rises by $> 50\%$ compared to pre-release baseline.
3. **Database Connection Pool Exhaustion:** Pool utilization exceeds 85%.
4. **Widget Session Failure:** `POST /widget/v1/session` failure rate $> 0.1\%$.

### Rollback Procedure
```powershell
# 1. Rollback application containers immediately
kubectl rollout undo deployment/fashx-backend -n prod
kubectl rollout undo deployment/fashx-worker -n prod

# 2. Invalidate CDN cache for widget script to previous version
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/static/widget/*"

# 3. Verify health endpoint
curl -f https://api.fashxstudio.com/healthz
```

---

## 6. Post-Release Verification

- [ ] Check `/healthz` and `/metrics` Prometheus endpoints.
- [ ] Verify test session creation from test merchant tenant.
- [ ] Confirm worker job processing rate and queue depth.
- [ ] Announce release completion in `#engineering-releases`.
