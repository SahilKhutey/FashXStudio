# RC13: Unit Economics & Operating Cost Model

> [!IMPORTANT]
> **Financial Governance Notice**: All cost, conversion, and revenue figures below represent planning assumptions and financial hypotheses, **not** measured FashXStudio financial actuals. Under `AGENTS.md` Rule 2, no revenue or commercial viability claim is verified until supported by executed merchant settlements and paid cloud provider invoices.

---

## 1. Unit Economics Hypothesis & Model

### A. Estimated Try-On Cost Breakdown
| Cost Category | Model Estimate | Notes / Unmeasured Factors |
|---|---|---|
| **Raw GPU Inference** | \$0.02 – \$0.05 / job (₹1.70 – ₹4.20) | Commercial endpoint pricing dependent on batching and volume commitments. |
| **Failed Jobs & Retries** | +10% – 15% overhead | Jobs failing decodability or GPU timeouts still incur compute cost. |
| **Queue & Worker Hosting** | ~\$0.005 / job (₹0.42) | Celery/Redis worker cluster overhead on cloud VMs. |
| **Storage & Bandwidth** | ~\$0.002 / job (₹0.17) | S3 PUT/GET requests and CDN egress for generated result artifacts. |
| **Total Estimated Marginal Cost** | **\$0.03 – \$0.06 / try-on** (₹2.50 – ₹5.00) | Full-cycle cost per completed try-on output. |

### B. User Allowance & Free Tier Exposure
- **Pilot Allocation**: 10–15 free try-ons per active pilot participant.
- **Estimated User Cost Cap**: Under \$0.60 – \$0.90 (₹50 – ₹75) per active monthly user.
- **Sustainability Boundary**: Offering perpetual free try-ons without confirmed affiliate monetization or subscription fees introduces substantial negative margin risk at scale.

---

## 2. Monetization Pathways & Merchant Economics

### A. Affiliate Commission Mechanics
- **Model Assumption**: 5% – 12% affiliate commission on gross merchandise value (GMV).
- **Assumed AOV (Apparel)**: ₹1,500 – ₹2,500.
- **Estimated Conversion Payout**: ₹75 – ₹250 per completed and retained purchase.

### B. Real Commercial Risks & Unmeasured Boundaries
1. **Redirect $\ne$ Revenue**: An outbound clickout via affiliate UTM link does not constitute a completed sale. Fashion return rates in India (25%–40%) and multi-day attribution windows mean that cookie drop-offs, return cancellations, and tracking pixel blocks severely discount realized affiliate payouts.
2. **Missing Partner Agreements**: FashXStudio does not yet possess executed commercial affiliate agreements with Myntra, Ajio, Amazon, or Tata CLiQ.
3. **Customer Acquisition Cost (CAC)**: Organic invite referral CAC is assumed low in closed pilots, but public acquisition CAC in Indian fashion tech ranges from ₹200 – ₹600 per acquired shopper, exceeding early affiliate payouts without strong multi-month retention.

---

## 3. Pilot Measurement & Invoice Accounting Protocol

During the Phase 10 closed pilot, actual financial telemetry must be recorded:
1. **Measured Inference Cost**: Invoices from the commercial GPU vendor must be tallied against total submitted jobs.
2. **Cost per Completed Try-On**: Total invoice cost divided strictly by completed, defect-free try-ons.
3. **Verified Purchase Attribution**: Track verified participant self-reported and partner-confirmed purchases to compute real GMV conversion.
