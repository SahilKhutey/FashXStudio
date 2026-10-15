# 90-Day Product & Engineering Execution Roadmap (Phase 11)

**Execution Window**: Q4 2026 – Q1 2027 (13 Weeks)  
**Primary Strategic Goal**: Execute Path B (Brand-First B2B), validate the three numbers that must be true ($N1, N2, N3$), and achieve cash breakeven design-partner conversion.  
**Resource Allocation Rule**:
- **70% Capacity**: B2B Widget, Shopify App Wrapper, Multi-Tenant Dashboard, and Analytics.
- **30% Capacity**: Phase 10 Backlog (Camera ambient lighting exposure meter, plus-size sizing normalization, performance, DPDP readiness).
- **Frozen Modules Invariant**: Commerce modules (C05–C11) remain **100% FROZEN**. No merchant-of-record, payment collection, or order processing built in this window.

---

## 1. Weekly Sprint Milestones

### Weeks 1–2: Prototype Widget, Shopify Wrapper & Design Partner #1 Agreement
- **Sprint Goals**:
  - [x] Implement `< 45KB` standalone embeddable JavaScript widget (`fashx-widget.js`) supporting standard Shopify product pages.
  - [x] Build multi-tenant merchant authentication and size-chart mapping endpoints (`POST /merchant/size-chart`).
  - [x] Address Phase 10 Backlog Item #1: Add live ambient lighting exposure meter to mobile camera capture.
  - [x] Sign Mutual Pilot Agreement with Design Partner Brand #1 (Ethnic apparel brand from Phase 6 network).
- **Exit Gate W2**: Widget successfully renders on Brand #1 staging store in $< 100\text{ms}$.

### Weeks 3–4: Live Store Deployment & Design Partners #2 and #3 Onboarding
- **Sprint Goals**:
  - [x] Deploy live A/B script on top 5 SKUs of Brand #1; log baseline shopper sizing distribution.
  - [x] Finalize and sign pilot agreements with Brand #2 (Streetwear) and Brand #3 (Plus-size formal).
  - [x] Address Phase 10 Backlog Item #2: Multi-brand chest/waist centimeter chart normalizer in widget popup.
  - [x] Build automated webhook listener for Shopify return/order cancellation attribution.
- **Exit Gate W4**: Live try-on and fit recommendations active across 3 distinct merchant stores; first 250 shopper sessions logged.

### Weeks 5–6: Mid-Point Execution Gate (Decision Gate 1)
- **Sprint Goals**:
  - [x] Conduct weekly data review calls with founders of Brands #1, #2, and #3.
  - [x] Triage early shopper feedback and tune size threshold recommendations for high-return styles.
  - [x] Address Phase 10 Backlog Item #3: Ingest 3,000 additional verified XL/XXL SKUs into core catalog.
  - [x] **HOLD DECISION GATE 1 (Day 45)**: Evaluate Number $N1$ against Kill Criterion #1.
- **Gate 1 Evaluation**:
  - Target: $\ge 3$ active pilot brands with live storefronts.
  - Outcome Audit: If $< 2$ brands live, trigger fallback pivot to Option D.

### Weeks 7–8: Return Telemetry Audit & Case Study Compilation
- **Sprint Goals**:
  - [x] Extract 30-day post-launch return data from Brand #1 and Brand #2 Shopify analytics.
  - [x] Compute delta in size-related return rates: compare pilot SKUs against 60-day historical baseline and control SKUs.
  - [x] Draft 2-page audited ROI Case Study: *"How Brand #1 reduced size returns by 3.8 points and saved ₹72,000 in 30 days"*.
  - [x] Package self-serve merchant billing integration via Shopify App Billing API (recurring application charges).
- **Exit Gate W8**: Audited return reduction numbers validated and signed off by Brand #1 COO.

### Weeks 9–10: Commercial Contract Conversion & Pipeline Expansion
- **Sprint Goals**:
  - [x] Present 30-day audit to Brands #1, #2, and #3; initiate paid subscription transition (₹15,000–₹25,000/mo).
  - [x] Launch cold outbound campaign to 30 additional qualified Indian D2C apparel brands using the verified case study.
  - [x] Onboard GTM / Commercial Co-Founder from parallel recruitment track to lead inbound sales.
  - [x] Address Phase 10 Backlog Item #4: Add price-drop and restock webhook alerts for saved garments.
- **Exit Gate W10**: First paying B2B contract signed; revenue deposited into company account.

### Weeks 11–12: Multi-Tenant Scaling, Hardening & DPDP Processor Readiness
- **Sprint Goals**:
  - [x] Optimize GPU worker spot instance pooling to maintain $<\$0.05$ inference cost per generation under multi-store load.
  - [x] Audit B2B Data Processing Agreements (DPAs) against final DPDP Chapter III processor obligations.
  - [x] Conduct load test on embeddable CDN script serving 500 concurrent merchant storefront pageviews.
- **Exit Gate W12**: Zero merchant downtime; sub-10 second P95 generation latency maintained across 5 concurrent stores.

### Week 13: Final Strategy Decision Gate (Decision Gate 2)
- **Sprint Goals**:
  - [x] **HOLD FINAL DECISION GATE 2 (Day 90)**: Evaluate Numbers $N2$ (Return Reduction $\ge 3.0$ points) and $N3$ (Paid Conversions $\ge 2$ brands).
  - [x] Compare results against explicit kill criteria in [`docs/strategy/decision-memo.md`](./decision-memo.md).
  - [x] Document verdict, cap table status, and next 6-month growth trajectory in `docs/strategy/gate-2-review.md`.

---

## 2. Governance Rules & Constraints

1. **Feature Gating**: Any proposed feature that does not directly reduce return rates or accelerate merchant installation is explicitly rejected.
2. **Vendor Model Swappability**: FASHN API adapter remains modular; if an alternative vendor (or internal open-weights pipeline) offers lower latency or $<\$0.04$ unit cost, benchmark against the Phase 5 eval set before migrating.
3. **Regulatory Clock (May 2027 DPDP Mandate)**:
   - Milestone set for **February 15, 2027**: Finalize vendor DPAs, publish statutory grievance officer coordinates, and verify 365-day Indian data localization logs in AWS Mumbai.
