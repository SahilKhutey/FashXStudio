# FashXStudio — Pilot Measurement Plan & Operational Schedule

**Document ID:** `FASHX-PLAN-001`  
**Version:** `1.0 — Execution Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.4 — Pilot Research Design & Sampling Cadence`  

---

## 1. Pilot Research Design & Sample Targets

The pilot is structured to produce high-confidence qualitative and technical evidence within a focused 4-week window without requiring mass-market consumer traffic.

| Research Dimension | Target Sample Size | Data Collection Method | Primary Owner |
| :--- | :--- | :--- | :--- |
| **Registration & Onboarding Usability**| 8–12 Shoppers | Moderated usability sessions + event telemetry | Product Manager / Mobile Lead |
| **Profile & Style Quiz Completion** | 8–12 Shoppers | Telemetry funnel analysis + user interviews | Product Manager |
| **Product Discovery & Search** | 10–15 Shoppers | Task-based usability tests (find a kurta/shirt) | UI/UX Lead |
| **VTO Technical Reliability** | $\ge 100$ Accepted Attempts | Server-side `vto_jobs` database logs | VTO / Backend Engineer |
| **Visual Realism & Preservation** | 30–50 Generated Results | Independent dual human reviewer panel | ML Engineer / Founder |
| **Digital Wardrobe & Handoff** | 10–15 Shoppers | Behavioral analytics + outbound click tracking| Product Manager |
| **Merchant Partner Onboarding** | 1–3 D2C Brands | White-glove integration sessions + interviews | Founder / B2B Lead |
| **Merchant Reporting Engagement** | 1–3 Merchants | Dashboard session logs + weekly review calls | B2B Operations |

---

## 2. Four-Week Pilot Measurement Schedule

```
Pre-Pilot Week 0: Instrumentation & Gate Verification
       │
       ▼
Week 1: Acquisition, Onboarding & User Photo Input Verification
       │
       ▼
Week 2: AI Try-On Quality, Latency & Error Decomposition
       │
       ▼
Week 3: Wardrobe Engagement, Outbound Handoff & Partner Utility
       │
       ▼
Week 4: Cost Accounting, Cohort Retention & Pilot Decision Review
```

### Detailed Milestone Cadence

- **Pre-Pilot (Week 0):** Verify end-to-end telemetry pipeline; confirm event schemas match `ANALYTICS_EVENT_SPECIFICATION.md`; conduct dry-run GPU inference using internal test accounts; test S3 deletion lifecycle; confirm zero PII leaks in logs.
- **Week 1 (Onboarding & Discovery):** Recruit initial cohort of 15 shoppers; measure registration completion rate and profile completion rate; audit photo input rejection reasons (lighting, pose, multi-person).
- **Week 2 (VTO Performance & Quality):** Execute 100+ try-on runs across Men's T-shirts, shirts, and kurtas; measure P95 latency and pipeline image failure rate; convene dual-reviewer panel to score 50 results against the Realism and Garment Preservation rubrics.
- **Week 3 (Commerce Handoff & Value):** Observe wardrobe save behavior; measure outbound redirect clicks to the partner merchant's store; conduct mid-pilot review with merchant founder to evaluate early impressions and product interest.
- **Week 4 (Financial Audit & Synthesis):** Calculate direct variable cost per completed try-on; analyze D7 retention cohort; compile the comprehensive Pilot Evaluation Report; present G1–G8 gate verdicts to the product owner.

---

## 3. KPI Ownership & Accountability Matrix

| Measurement Domain | Accountable Role | Daily Cadence | Weekly Review Meeting |
| :--- | :--- | :--- | :--- |
| **Onboarding & Registration** | Mobile Engineer | Monitor verification error spikes | Monday Product Standup |
| **Catalog Feed Ingestion** | Ingestion Engineer | Monitor failed sync jobs | Monday Product Standup |
| **VTO Pipeline & GPU Latency** | VTO / Backend Lead | Daily latency P95 & failure rate audit | Wednesday Technical Review |
| **Visual Quality & Realism** | ML Engineer / Founder | Sample review of flagged outputs | Wednesday Technical Review |
| **Merchant Success & Handoff**| B2B Lead / Founder | Monitor outbound redirect clicks | Friday Partner Review |
| **Infrastructure & Unit Cost** | DevOps / FinOps Lead | Review daily GPU burn vs ₹5,000 ceiling| Friday Financial Review |
