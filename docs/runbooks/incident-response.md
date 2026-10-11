# Incident Response Runbook

## 1. Overview & Severity Definitions

This runbook guides incident response for production disruptions at FashXStudio.

| Severity | Definition & Impact | Response SLA | Comms Cadence | Escalation Path |
| :--- | :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | Core user flow completely broken: feed unreachable (>50% users), authentication down, data breach suspected, or cascading 5xx errors. | **15 minutes** | Updates every 30m to `#incident-prod` & status page | Incident Commander (IC), Lead Eng, Legal Counsel (if breach) |
| **SEV-2 (Major)** | Degraded service: virtual try-on failing (>15%), P95 feed latency >600ms, Celery background worker hung, third-party provider degraded. | **30 minutes** | Updates every 60m to `#incident-prod` | On-call Engineer, IC |
| **SEV-3 (Minor)** | Non-blocking issues: slow admin reporting, minor UI anomaly, non-paging warnings, transient rate-limit spikes. | **4 hours** | Next business day update in `#eng-alerts` | Feature owner / Eng team |

---

## 2. Immediate Containment (First 15 Minutes)

1. **Acknowledge Alert**: Acknowledge page in alerting system and announce in Slack `#incident-prod`.
2. **Designate Incident Commander (IC)**: IC owns triage, communication, and delegating fixes.
3. **Check System Health**:
   - Query `/healthz/ready` and inspect dependency state (`postgres`, `redis`, `jwks`).
   - Open AWS CloudWatch dashboard for ECS Fargate service `fashx-api` and RDS instance `fashx-prod-db`.
4. **Determine Triage Action**:
   - If issue coincides with a recent deployment: **Trigger immediate rollback** (see [`deploy-and-rollback.md`](./deploy-and-rollback.md)).
   - If database connection spike or CPU >90%: Scale Fargate tasks or tune connection pool.
   - If external try-on provider failing: Flip `tryon_enabled` kill switch to `False` (see [`vendor-outage.md`](./vendor-outage.md)).

---

## 3. Diagnosis & Mitigation Steps

- **Inspect Logs**: Run structured CloudWatch log query filter:
  `fields @timestamp, request_id, user_id, level, message, error_code | filter level = "ERROR" | sort @timestamp desc | limit 50`
- **Check Database Locks & Slow Queries**:
  `SELECT pid, age(clock_timestamp(), query_start), usename, query FROM pg_stat_activity WHERE state != 'idle' AND query NOT ILIKE '%pg_stat_activity%' ORDER BY age desc;`
- **Mitigate**: Apply targeted mitigation (scale tasks, rotate secret, isolate affected worker queue).

---

## 4. Communication Templates

### Internal Update (Slack `#incident-prod`):
> **[SEV-1] Incident Update #1 - Feed Outage**  
> **Status**: Investigating  
> **Impact**: Users experiencing 500 errors on the discovery feed.  
> **Current Actions**: Rolling back ECS deployment to git SHA `c093b7a`.  
> **Next Update**: 15 minutes.  
> **IC**: @founder

### External Status Page:
> **Investigating Service Degradation**  
> We are actively investigating an issue affecting garment discovery and styling recommendations. Virtual try-on and profile services may be temporarily unavailable. Our engineering team is currently deploying a mitigation.

---

## 5. Post-Incident Review (PIR / Postmortem)

A blameless postmortem must be published to `docs/logs/postmortems/` within 48 hours for all SEV-1 and SEV-2 incidents, containing:
1. Executive Summary & Impact (duration, users affected, revenue/cost impact).
2. Timeline of events (detection, containment, recovery).
3. Root cause analysis (5 Whys).
4. Corrective and preventive action items with owners and due dates.
