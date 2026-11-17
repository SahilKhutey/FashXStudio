# FashXStudio — Virtual Try-On Unit Economics & Cost Tracking

**Document ID:** `FASHX-OPS-001`  
**Version:** `1.0 — Execution Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.4 — Financial Sustainability & Infrastructure Accounting`  

---

## 1. Unit Economics Philosophy

A technically functional virtual try-on product is commercially non-viable if the marginal cost of delivering an image generation exceeds the revenue generated from merchant subscriptions and try-on fees. 

FashXStudio mandates strict cost accounting based on **actual provider invoices, retries, and storage consumption**, rather than assuming theoretical base vendor prices.

---

## 2. Cost Calculation Formulas

### A. Direct Variable Cost Per Completed Try-On ($C_{\text{VTO}}$)

$$C_{\text{VTO}} = C_{\text{provider}} + C_{\text{storage}} + C_{\text{compute}} + C_{\text{infrastructure}}$$

Where:
- **$C_{\text{provider}}$:** Total GPU API fees incurred across all attempts required to complete the job:
  $$C_{\text{provider}} = \text{Unit API Rate} \times \text{Attempts (including failed retries)}$$
- **$C_{\text{storage}}$:** S3/R2 PUT charges, GET egress bandwidth, thumbnail generation, and 30-day lifecycle storage cost.
- **$C_{\text{compute}}$:** Celery background worker container CPU/RAM allocation during preprocessing and quality checks.
- **$C_{\text{infrastructure}}$:** Redis message broker overhead and database write IOPS.

### B. Fully Loaded Pilot Operating Cost Per Try-On ($C_{\text{loaded}}$)

$$C_{\text{loaded}} = \frac{\sum \text{Direct Variable Costs} + \sum \text{Attributable Fixed Pilot Infrastructure}}{\text{Total Successfully Delivered VTO Jobs}}$$

Fixed pilot costs include staging server instances, base database hosting, observability tooling (Sentry/Datadog), and domain/security certificates.

---

## 3. Illustrative Pilot Budget Ceiling & Margin Targets

| Cost Component | Budget Ceiling Target (Per Try-On) | Current Tracking Basis |
| :--- | :--- | :--- |
| **FASHN GPU API Fee** | $\le ₹8.50$ (Approx. \$0.10 USD) | Tracked via `vto_jobs.provider_cost` |
| **Object Storage & Bandwidth** | $\le ₹0.75$ | S3 invoice allocation per GB transferred |
| **Worker Compute & Redis** | $\le ₹1.50$ | Cloud VM instance runtime allocation |
| **API Gateway & DB Query Overhead**| $\le ₹0.75$ | Managed Postgres & app server allocation |
| **Total Direct Variable Cost ($C_{\text{VTO}}$)**| $\le ₹11.50$ | Target ceiling for pilot operations |

### Target Gross Margin
At a planned pilot billing rate of **₹30.00 to ₹35.00** per try-on unit (or bundled equivalent in merchant SaaS plans):

$$\text{Gross Margin} = \frac{₹35.00 - ₹11.50}{₹35.00} \times 100 \approx 67.1\%$$

*Minimum Commercial Gate:* FashXStudio must maintain a gross margin $\ge 65\%$ on all usage-based try-on tiers.

---

## 4. Cost Guardrails & Automated Alerts

1. **Daily Burn Ceiling:** If aggregate GPU provider spend exceeds ₹5,000 in a 24-hour window on staging/pilot, an automated PagerDuty/Slack alert triggers.
2. **Per-Shopper Rate Limiting:** Daily try-ons are capped at 5 generations per user per day in the free consumer tier.
3. **Retry Cost Cap:** Jobs are permitted at most 1 automated retry. If attempt #2 fails, the job terminates immediately to prevent runaway API fees.
4. **Idempotency Enforcement:** Prevents accidental double-taps by users from triggering duplicate GPU invocations.
