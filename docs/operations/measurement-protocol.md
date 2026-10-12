# B2B Return-Reduction Measurement Protocol

- **Version:** 1.0 (Phase 12 Path B Execution)
- **Target Outcome:** Defensible, statistically valid proof of return reduction ($\ge 3.0$ percentage points) for Indian D2C apparel brands.

---

## 1. The Measurement Challenge

Measuring return reduction in fashion ecommerce is prone to selection bias: shoppers who engage with sizing tools may already be more cautious or intentional buyers.

To isolate true causality and present unassailable return ROI to brand CFOs and heads of ecommerce, FashXStudio enforces a **Difference-in-Differences (DiD) quasi-experimental measurement protocol** across all live partner storefronts.

---

## 2. Methodology & Experimental Design

### A. Matched Cohort Design
For every partner brand running the FashXStudio storefront widget, transactions are partitioned into two strictly comparable cohorts over identical 30-day billing cycles:

1. **Cohort E (Exposed / Assisted):**
   - Shoppers on PDPs who opened the FashXStudio widget, completed a virtual fit simulation, and purchased the recommended size.
2. **Cohort C (Control / Baseline):**
   - Shoppers who purchased the exact same SKUs during the same time window without FashXStudio fit assistance (via matched PDP traffic split or historical pre-launch baseline adjusted for seasonal return drift).

### B. Difference-in-Differences (DiD) Estimator

$$\Delta \text{Return Rate} = (\bar{R}_{E,\text{post}} - \bar{R}_{E,\text{pre}}) - (\bar{R}_{C,\text{post}} - \bar{R}_{C,\text{pre}})$$

Where:
- $\bar{R}$: Gross Return Rate ($\frac{\text{Returned Units}}{\text{Delivered Units}}$).
- Return window: 14 calendar days post-delivery (standard Indian D2C window).

---

## 3. Financial Impact & Value Quantification

For every verified point of return reduction, value is calculated using the brand's verified reverse logistics cost:

$$\text{Monthly Out-of-Pocket Savings} = \text{Monthly Orders} \times \Delta \text{Return Rate} \times \text{Cost per Return (₹350)}$$

### Example Calculation (House of Indya Baseline):
- Monthly Online Orders: 18,000 units
- Baseline Return Rate: 31.2% (5,616 returned units)
- Return Rate with FashXStudio: 27.8% (4,992 returned units)
- **Net Returns Prevented:** $624\text{ units}$
- **Gross Monthly Cost Savings:** $624 \times ₹350 = \mathbf{₹2,18,400 / \text{month}}$
- **FashX SaaS Subscription Fee:** ₹18,000 / month
- **Net Brand ROI:** $\mathbf{12.1\times}$ return on software spend.

---

## 4. Verification & Audit Sign-Off

1. **Shopify Order & Return Webhook Sync:**
   - Real-time webhook ingestion: `orders/fulfilled`, `refunds/create`, `returns/approve`.
2. **Attribution Tagging:**
   - Order line items retain cart attribute `_fashx_session_token` and `_fashx_recommended_size`.
3. **Monthly Joint Sign-Off:**
   - Automated report exported on the 1st of each month via `/merchant/analytics`.
   - Brand ecommerce manager and FashXStudio account lead sign off on verified savings.
