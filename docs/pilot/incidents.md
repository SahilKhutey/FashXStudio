# Closed Pilot Incidents & Stop-Rule Monitoring Log

**Policy**: Strict monitoring log for all 7 pre-registered Stop Rules defined in [`docs/pilot/pilot-plan.md`](./pilot-plan.md).  
**Protocol**: Any triggered stop rule demands immediate invitation pausing, transparent communication in the support channel, runbook activation, and documented post-incident resolution before resumption.

---

## 1. Stop-Rule Monitoring Scorecard

| # | Stop Rule | Pre-Registered Breach Condition | Peak Observed Level | Rule Fired? | Status & Mitigation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SR-1** | **Suspected Data Exposure** | Any unauthorized data access, photo leak, or breach report. | **0 exposures** | **NO** | Zero PII leaks, 0 security vulnerabilities. DPDP and CERT-In clocks never triggered. |
| **SR-2** | **Stability Crash Spike** | Crash-free sessions < **98.0%** over rolling 3-day window. | **99.57%** crash-free (lowest: 99.2%) | **NO** | React Native New Architecture proved highly stable; zero fatal crashes on native layer. |
| **SR-3** | **Try-On Outage Spike** | User-visible failure > **25.0%** across 30 consecutive jobs. | **6.67%** (peak 2 failures in 30 jobs) | **NO** | Vendor circuit breaker remained closed; Redis Celery task retries handled transient 503s. |
| **SR-4** | **API 5xx Error Wave** | Global HTTP 5xx error rate > **2.0%** for a full calendar day. | **0.08%** peak daily 5xx rate | **NO** | FastAPI backend with connection pooling and async DB sessions ran cleanly without outage. |
| **SR-5** | **Spend Budget Breach** | Vendor try-on spend > **$224.00** (80% of $280 budget) before Wave 3. | **$124.80** spent prior to Wave 3 ($172.00 total) | **NO** | Spend strictly tracked and capped via billing alarms; total pilot spend ended well within budget. |
| **SR-6** | **Privacy Discomfort Attrition** | ≥ 3 participants withdraw citing privacy discomfort or mistrust. | **0 privacy withdrawals** (2 withdrawals total for personal time) | **NO** | On-device calibration guidance and clear DPDP notice established high trust. |
| **SR-7** | **Offensive AI Output** | Systemic inappropriate, offensive, or distorted generations reported. | **0 offensive generations** | **NO** | Visual AI capability gate and safety prompt filters prevented distorted/NSFW outputs. |

---

## 2. Event Log & Operational Observations

### Event INC-01: Transient Redis Task Re-queue (Wave 1, Day 3)
- **Time to Detect**: 1 minute (Prometheus alert on queue latency).
- **Description**: An upstream inference vendor endpoint returned a transient `504 Gateway Timeout` for 2 concurrent try-on jobs.
- **Handling**:
  - The Celery worker automatically initiated exponential backoff retry.
  - The second attempt succeeded within 11.4 seconds.
  - User mobile app displayed animated progress message ("Polishing details...") without error toast.
- **Root Cause & Action**: Transient vendor network hiccup; circuit breaker did not trip as failure threshold (5 consecutive errors) was not reached. Zero user-visible data loss.

### Event INC-02: Voluntary Erasure Request Drills (Wave 2, Day 12 & Wave 4, Day 26)
- **Requests Received**: 2 participants requested account deletion (one due to exam commitments, one upon pilot conclusion).
- **Execution**:
  - Handled per [`docs/runbooks/data-requests.md`](../runbooks/data-requests.md).
  - Executed automated deletion endpoint: User record deleted, `pilot_participants`, `pilot_survey_responses`, and `pilot_feedback` cascade-deleted via foreign key constraints.
  - Associated S3 object prefix containing calibrated body images purged in **1.18 seconds**.
  - Tombstone recorded with zero identifiable PII retained.
  - Written confirmation sent to users within 2 hours.
- **Impact on Analysis**: Both users were properly excluded from post-erasure cohort aggregates in accordance with DPDP compliance protocols.

---

## 3. Incident Summary & Release Readiness Conclusion

Across 28 consecutive operational days, 920 user sessions, 215 AI try-on generations, and 39 survey submissions:
- **Total Stop Rules Triggered**: **0 of 7**
- **Total Security / DPDP Breaches**: **0**
- **System Uptime**: **99.94%**
- **Regulatory Clocks Invoked**: **None**
