# RC08 — Observability, Metrics & Service Level Objectives

## 1. Structured Logging
All backend services output single-line JSON logs with correlated trace metadata:
```json
{
  "timestamp": "2026-11-05T10:30:00.123456+00:00",
  "level": "INFO",
  "logger": "fashx.api.v1.tryon",
  "message": "Try-on job submitted successfully: job_id=abc-123 user_id=usr-456",
  "request_id": "req-987",
  "trace_id": "tr-654"
}
```
**PII redaction**: Personal photo binary bytes, signed URL tokens, access tokens, and exact body circumferences are strictly excluded from logs.

## 2. Pilot Service Level Objectives (SLOs)
| Metric | Pilot Target | Budget Window | Calculation / Source |
|---|---|---|---|
| API Availability | ≥ 99.5% | 30 days rolling | Successful requests (`<500`) / Total requests |
| Feed API p95 Latency | ≤ 800 ms | 7 days rolling | `http_request_duration_seconds{endpoint="/api/v1/feed"}` |
| General API Error Rate | < 1.0% | 1 hour window | 5xx responses / total responses |
| VTO Job Processing Success | ≥ 95.0% | 24 hours rolling | Succeeded jobs / (Total jobs - User canceled) |
| VTO Async Duration p95 | ≤ 45 seconds | 24 hours rolling | Time from job submission to result available |
| Zero Cross-User Leakage | 0 incidents | Continuous | Hard stop: unauthorized cross-user access |

## 3. High-Priority Alert Rules
1. **HighApiErrorRate**: API error rate > 5% over 5 minutes (Severity: Critical).
2. **ElevatedApiLatency**: Feed API p95 latency > 1500 ms for 10 minutes (Severity: Warning).
3. **QueueBacklogCritical**: Celery queue depth > 50 jobs for 15 minutes (Severity: Critical).
4. **VTOProviderErrorRate**: Provider failure rate > 15% for 15 minutes (Severity: Warning).
