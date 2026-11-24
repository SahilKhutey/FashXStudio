# Monitoring, Observability & Alerting Architecture

## 1. Metrics Design Principles

Virtual Try-On telemetry strictly enforces low-cardinality, non-PII conventions:
- **Zero PII**: No user IDs, merchant names, product IDs, image hashes, or S3 URIs in metric tags or labels.
- **Allowed Dimensions**: `Provider`, `Model`, `Outcome`, `Status`, `LimitType`, `ScopeType`, `Operation`.

---

## 2. Prometheus / CloudWatch Metrics Catalog

| Metric Name | Type | Unit | Dimensions | Description |
|---|---|---|---|---|
| `TryOnCacheLookups` | Counter | Count | `Provider`, `Outcome` | Cache hit/miss/expired/invalidated lookup frequency. |
| `TryOnProviderSpendUSD` | Counter | USD | `Provider`, `Operation`, `Status` | Total realized dollar expenditure on third-party inference. |
| `TryOnRateLimitRejections` | Counter | Count | `LimitType` | Count of requests throttled by rate limiters. |
| `TryOnBudgetReservations` | Counter | USD | `ScopeType`, `Status` | Value of reservations created, committed, or released. |
| `TryOnBudgetUtilizationPct` | Gauge | Percent | `ScopeType` | Active percentage of budget capacity utilized. |

---

## 3. CloudWatch Alarms & PagerDuty Rules

```
+--------------------------------------------------------------------------+
| CloudWatch Alarm: TryOnBudgetWarning70                                   |
| Metric: TryOnBudgetUtilizationPct >= 70% for 5 consecutive minutes       |
| Severity: WARNING                                                        |
| Action: Slack alert to #eng-vto-spend                                    |
+--------------------------------------------------------------------------+

+--------------------------------------------------------------------------+
| CloudWatch Alarm: TryOnBudgetCritical90                                  |
| Metric: TryOnBudgetUtilizationPct >= 90% for 2 consecutive minutes       |
| Severity: CRITICAL                                                       |
| Action: PagerDuty alert to Primary On-Call                               |
+--------------------------------------------------------------------------+

+--------------------------------------------------------------------------+
| CloudWatch Alarm: TryOnRateLimitSurge                                    |
| Metric: TryOnRateLimitRejections > 100/min                              |
| Severity: WARNING                                                        |
| Action: Investigate bot traffic / catalog scraping activity             |
+--------------------------------------------------------------------------+
```
