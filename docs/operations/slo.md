# Service Level Objectives (SLOs) & Error Budget Policy

- **Version:** 1.0 (Production & B2B Operations)
- **Effective Date:** Phase 12 (Day 1)
- **Review Cadence:** Monthly

---

## 1. Principles & Measurement Windows

Our SLOs protect two critical experiences:
1. **Shoppers on Brand PDPs:** Must experience zero noticeable page lag, lightning-fast modal responses, and reliable try-on generation.
2. **Brand Merchants:** Must have uninterrupted access to fit analytics, catalog sync, and configuration portals.

**Measurement Window:** Rolling 30 calendar days.  
**Measurement Method:** Continuous automated probes from multiple Indian metro locations (Bengaluru, Mumbai, Delhi-NCR) + server-side synthetic & real-user monitoring.

---

## 2. Core Service Level Indicators (SLIs) & Objectives (SLOs)

| Service Area | Indicator (SLI) | Target (SLO) | Error Budget (30d) |
|---|---|---|---|
| **Widget CDN Asset** | Successful HTTP 200/304 requests for `fashx-widget.js` | $\ge 99.95\%$ | 21.6 minutes outage / 0.05% bad reqs |
| **Widget Script Init Latency** | Time to execute initialization script in shopper DOM | p95 $< 25\text{ms}$, p99 $< 50\text{ms}$ | 1.0% slow initializations |
| **Widget Session API** | Success rate for `POST /widget/v1/session` | $\ge 99.90\%$ | 0.10% failed requests |
| **Widget Session Latency** | Round-trip response time for session token issuance | p95 $< 120\text{ms}$, p99 $< 300\text{ms}$ | 1.0% requests exceeding 300ms |
| **Try-On Generation Reliability** | Try-on pipeline job completed successfully without timeout | $\ge 98.50\%$ | 1.50% failed generation jobs |
| **Try-On Generation Latency** | Time from garment/photo submission to returned image artifact | p50 $< 8.0\text{s}$, p95 $< 15.0\text{s}$ | 5.0% jobs exceeding 15.0s |
| **Merchant Dashboard** | HTTP 2xx on `/merchant/dashboard` and `/merchant/analytics` | $\ge 99.90\%$ | 43.2 minutes downtime |
| **DPDP Erasure SLA** | Biometric media purge completed within scheduled window | $100\%$ within 24h | Zero tolerance (regulatory compliance) |

---

## 3. Error Budget Policy

Error budgets prevent over-indexing on velocity at the expense of merchant trust and shopper experience.

### Budget Consumption Tiers
1. **Green (< 50% budget burned):** Normal operating velocity. Feature deployment proceeds without restrictions.
2. **Yellow (50% – 80% budget burned in 7 days):**
   - Release train slows; requires Head of Engineering approval for non-critical features.
   - Root-cause analysis (RCA) required for the incidents consuming the budget.
3. **Orange (80% – 99% budget burned):**
   - Feature freeze on affected services.
   - All PRs must be reliability, performance, or bug-fix related.
4. **Red (100% budget exhausted):**
   - **Full Feature Freeze:** Zero feature releases until error budget recovers above 20% over a 7-day rolling window.
   - 100% of engineering bandwidth reallocated to infrastructure stability, caching, worker resilience, or query optimization.

---

## 4. Alerting & Escalation Matrix

- **Page (P1 - Urgent):**
  - Widget error rate $> 1.0\%$ over 5 minutes.
  - Try-on failure rate $> 5.0\%$ over 10 minutes.
  - API p99 latency $> 1000\text{ms}$ over 5 minutes.
  - Immediate notification to on-call rotation.
- **Slack Alert (P2 - Degraded):**
  - Error budget burn rate $> 2\times$ baseline.
  - Worker queue depth $> 50$ jobs backlog for $> 5$ minutes.
  - Storage bucket cleanup job skipped or failed.
- **Daily Digest (P3 - Informational):**
  - Daily error budget status report posted to `#ops-reliability`.
