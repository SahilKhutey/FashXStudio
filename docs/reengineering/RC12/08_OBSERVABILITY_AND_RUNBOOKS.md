# RC12: Observability, Alerts and Runbooks

## 1. Core Health Dashboards
- **API Health**: Request rate, latency percentiles (p50, p95, p99), HTTP 5xx error rate.
- **Database & Queue**: Active connection pool saturation, pgvector query latency, Redis queue backlog age.
- **VTO Monitoring**: Success rate, queue duration, inference latency, cumulative vendor spend.
- **Catalog Operations**: Ingestion sync timestamps, duplicate candidates, stale price percentage.

## 2. Severity Levels & Incident Runbooks
- **SEV-1 (Critical Outage / Data Leak)**:
  - Suspected photo/data exposure or API 5xx $>2\%$.
  - Action: Toggle emergency kill switch, invoke CERT-In 6-hour breach response runbook, halt invitations.
- **SEV-2 (Feature Degradation)**:
  - VTO queue failure $>25\%$ or spend $>80\%$ of budget.
  - Action: Freeze new job dispatch, inspect vendor circuit breaker, switch mobile to fallback preview.
- **SEV-3 (Catalog / Data Drift)**:
  - Stale prices $>15\%$ in active feed.
  - Action: Trigger partner feed re-sync, suppress affected products from discovery.
