# RC08 — Incident Response & Triage Runbook

## 1. Severity Classifications
- **SEV-1 (Critical Outage / Breach)**: Cross-user data leakage, unauthenticated personal photo access, complete API failure (>50% error rate), database corruption. Page on-call immediately; hard stop on all pilot operations.
- **SEV-2 (Major Impairment)**: Virtual Try-On inference provider down, Celery worker queue stalled, API error rate >5%. Response within 30 minutes.
- **SEV-3 (Moderate Impairment)**: Background catalog ingestion failure, transient Redis connectivity hiccups, localized UI glitches. Response within 4 hours.
- **SEV-4 (Minor Issue)**: Non-critical cosmetic bug, minor analytics latency. Triage in normal business hours.

## 2. Triage & Escalation Procedures
1. **Detect & Confirm**: Alert fired in Slack / PagerDuty. Verify `/healthz/ready` and Datadog / CloudWatch metrics.
2. **Mitigate & Isolate**:
   - For VTO provider failure: Set `TRYON_ENABLED=false` or fail open with graceful UI maintenance notice.
   - For data leakage / exploit: Immediately revoke compromised tokens and terminate suspicious sessions.
   - For bad release: Execute rollback script (`PREV_TAG`).
3. **Resolve & Verify**: Confirm error rate returns below 1% and `/healthz/ready` reports green across all dependencies.
4. **Post-Mortem**: Document root cause, timeline, impact, and preventive action items within 48 hours.
