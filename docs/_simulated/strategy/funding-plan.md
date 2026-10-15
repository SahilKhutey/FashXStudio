# Capital Strategy & Funding Plan (Phases 11–12)

**Core Principle**: Capital is an accelerant, not a milestone. We fundraise only against pre-validated operational proof, maintaining capital efficiency and avoiding premature dilution before product-market fit.

---

## 1. Investor Readiness Checklist

Before presenting to any external angel, accelerator, or institutional investor, the following requirements must be verified:

- [x] **Validated Decision Memo & 90-Day Plan**: Completed in [`docs/strategy/decision-memo.md`](./decision-memo.md) and [`90-day-plan.md`](./90-day-plan.md) with explicit kill criteria.
- [x] **Verified Pilot Telemetry**: Audited numbers with 95% Wilson confidence intervals documented in [`docs/pilot/pilot-report.md`](../pilot/pilot-report.md).
- [x] **Production Security & Privacy Package**: Phase 9 OWASP compliance, DPIIT/DPDP ready architecture, zero PII retention in logs.
- [x] **Unencumbered IP & License Provenance**: 100% verified model licensing (commercial DPA on FASHN API; Rule I08 non-commercial models banned); clean repository ownership.
- [ ] **Incorporated Legal Entity**: Private Limited company incorporated in India (scheduled Month 2 upon co-founder selection).
- [ ] **DPIIT Startup Recognition**: Free application filed via Startup India portal immediately post-incorporation.
- [ ] **Audited Cap Table & IP Assignment**: Formal IP assignment agreement executed between founders and the incorporated entity.

---

## 2. Capital Stack & Staged Funding Tranches

```
[Tranche 0: Bootstrap + $25k Credits] ──► [Tranche 1: Non-Dilutive SISFS Grant] ──► [Tranche 2: Pre-Seed / Accelerator]
       (Months 1–3: $0 dilution)               (Months 3–6: ₹20–50 Lakhs)               (Months 6–9: ₹1.5–2.0 Cr)
```

### Tranche 0: Bootstrap & Non-Dilutive Cloud Credits (Months 1–3)
- **Founder Capital**: ₹1,50,000 personal allocation covering basic legal incorporation, CA retainers, domain/email, and monthly GPU inference.
- **Cloud & AI Credits**:
  - **AWS Activate Founders**: $1,000 to $5,000 in AWS cloud infrastructure credits (offsets RDS, ECS, and S3 costs for 6+ months).
  - **Google for Startups Cloud Program**: Up to $2,000 in credits.
  - **OpenAI / Anthropic Startup Credits**: Covers VLM catalog enrichment calls.
- **Objective**: Reach 3 live B2B brand pilots and validate return reduction with **zero equity dilution**.

### Tranche 1: Government Non-Dilutive Grants (SISFS Scheme) (Months 3–6)
- **Program**: **Startup India Seed Fund Scheme (SISFS)** administered via accredited incubators (e.g., IIM Bangalore NSRCEL, IIT Delhi, or CIE IIIT Hyderabad).
- **Grant Mechanism**:
  - Up to **₹20 Lakhs INR** (~$24,000 USD) as a 100% equity-free grant for validation of proof of concept, prototype development, and product trials.
  - Optional follow-on of up to **₹50 Lakhs INR** via convertible debentures / debt.
- **Statutory Eligibility Requirements**:
  - DPIIT-recognized startup incorporated within the last 2 years.
  - Minimum 51% Indian promoter shareholding (satisfied).
  - Innovative tech-driven solution with measurable market impact.
- **Action Plan**: File DPIIT recognition in Week 6; submit SISFS incubator application by Week 8.

### Tranche 2: Institutional Pre-Seed / Co-Founder Residency (Months 6–9)
- **Target Ask**: **₹1.50 Cr to ₹2.00 Cr INR** (~$180,000 – $240,000 USD) at a post-money valuation of ₹12 Cr – ₹16 Cr.
- **Target Programs & Investors**:
  1. **Antler India Residency**: Provides structured co-founder pairing, ~₹2 Cr pre-seed capital for ~9% equity, and direct access to domestic D2C brand networks.
  2. **Top-Tier Indian Fashion & D2C Angels**: Founders of established Indian D2C apparel brands, ex-Myntra/Ajio VP-level executives, and logistics tech angels (who immediately understand the ₹350/return pain).
  3. **Y Combinator (S27 Cohort) / Peak XV Surge**: Apply once 3 paying brand contracts and audited return-reduction case studies are achieved.

---

## 3. Use of Funds & 12-Month Runway Allocation

*(Based on target Tranche 1 + Tranche 2 pre-seed pool of ₹1.80 Cr INR / $215k USD)*

| Expenditure Category | Share (%) | 12-Month Allocation (INR) | Strategic Milestone Funded |
| :--- | :---: | :--- | :--- |
| **Engineering & Product R&D** | 45% | ₹81,00,000 | Founder stipends, 2 full-stack engineers, GPU spot cluster optimization, and automated size-chart parsing. |
| **Sales, GTM & Merchant Success**| 30% | ₹54,00,000 | Commercial co-founder stipend, B2B outbound tooling, Shopify App Store marketing, customer success lead. |
| **Cloud, GPU & Data Infrastructure**| 15% | ₹27,00,000 | Scaled inference capacity for 50+ concurrent merchant stores, Redis cluster, S3/R2 storage. |
| **Legal, Compliance & DPDP Audit**| 10% | ₹18,00,000 | Outside counsel retainers, trademark registrations, DPDP independent security audit, CA/auditor fees. |
| **Total** | **100%** | **₹1,80,00,000 INR** | **14 Months Runway $\to$ Target ₹25L MRR ($300k ARR)** |

---

## 4. Key Decision Gates for Capital

- **Gate A (Day 60)**: If 3 B2B pilots are live and showing positive return trend $\to$ Formally submit SISFS grant application and Antler India residency application.
- **Gate B (Day 90)**: If at least 2 brands convert to paid subscriptions ($\ge\text{₹15,000/mo}$) $\to$ Open angel syndicate round for ₹50–75 Lakhs bridge or proceed with accelerator term sheet.
- **Gate C (Day 90 Kill Condition)**: If pilot brands reject paid conversion $\to$ Pause all institutional fundraising; preserve cash and execute strategic pivot.
