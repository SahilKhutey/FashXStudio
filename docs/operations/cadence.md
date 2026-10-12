# Operational & Maintenance Cadence

- **Version:** 1.0
- **Team:** FashXStudio Engineering & Operations
- **Scope:** Maintenance rhythms, audit cycles, and operational health

---

## 1. Cadence Overview

To maintain product velocity while protecting B2B service reliability and regulatory posture, engineering operates on four structured cadences:

```
Weekly Ops Review (Mondays 10:00 IST)
  ↳ Metrics Tree, Error Budgets, Merchant Health, Incident Post-mortems

Monthly Compliance & Security Audit (1st Wednesday)
  ↳ DPDP Log Audits, Dependency CVE Scan, Cost Reconciliation, Secret Rotation

Quarterly Strategic Review & Gate Check (Every 12 Weeks)
  ↳ Gate Progress, Capacity Planning, Competitive Model Benchmarking, DR Drill

Annual Audit (May)
  ↳ Statutory DPDP Assessment, SOC2 Type II readiness, Comprehensive Penetration Test
```

---

## 2. Weekly Maintenance Cadence

**Schedule:** Every Monday at 10:00 IST (45 mins)  
**Attendees:** Engineering Lead, Operations Lead, Founder

### Agenda
1. **North Star & Input Metric Review:**
   - Active partner brands with live widget & valid impressions.
   - Return rate delta & try-on completion rates across active brand cohorts.
2. **SLO & Error Budget Health:**
   - Review 30-day rolling error budgets for CDN, Session API, and Try-on generation.
   - Authorize or lift any release restrictions based on `docs/operations/slo.md`.
3. **Merchant Health & Support Queue:**
   - Unresolved merchant tickets, onboarding blockers, and custom CSS theme friction.
4. **Action Item Tracking:**
   - Assign owners to operational tasks; review progress on open post-mortems.

---

## 3. Monthly Operational Cadence

**Schedule:** First Wednesday of every calendar month (60 mins)

### Tasks
- **Security & Dependency Hygiene:**
  - Run `pip audit`, `npm audit`, and Trivy container vulnerability scans.
  - Patch any critical/high CVEs within 72 hours.
- **Data Protection & Erasure Audit:**
  - Verify that 100% of ephemeral shopper session artifacts older than 24 hours have been completely expunged from S3/MinIO.
  - Audit `erasure_tombstones` and ensure zero unclassified tables in `backend/fashx/application/erasure.py`.
- **Infrastructure & Cloud Cost Reconciliation:**
  - Audit AWS/GPU cluster bill against `docs/operations/cost-guardrails.md`.
  - Terminate orphaned preview environments, idle dev workers, and unattached EBS volumes.
- **Tenant Usage & Billing Audit:**
  - Run `scripts/operations/views.sql` `v_tenant_usage` to verify merchant quotas and compute credit margins.

---

## 4. Quarterly Strategic Review

**Schedule:** End of Weeks 12, 24, 36, 48 (Half-day)

### Tasks
- **Disaster Recovery (DR) Simulation:**
  - Tabletop drill or chaos engineering test: simulate GPU worker regional outage and database failover.
  - Verify Recovery Time Objective (RTO $< 15\text{min}$) and Recovery Point Objective (RPO $< 1\text{min}$).
- **Garment & Try-On Quality Re-benchmarking:**
  - Run standardized 100-look evaluation across Sarees, Kurtas, Westernwear, and Formalwear against latest Google Shopping and competitive alternatives.
  - Verify FashXStudio maintains $\ge +0.75$ visual score advantage on Indian ethnic wear.
- **Capacity & Scaling Forecast:**
  - Project merchant onboarding pipeline for upcoming quarter; secure GPU reserved instance commitments if utilization trends $\ge 70\%$.
