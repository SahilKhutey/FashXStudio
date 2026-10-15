# Experiment Pre-Registration: widget_cta_v1

- **Experiment Identifier:** `widget_cta_v1`
- **Owner:** Product & Growth Engineering
- **Status:** Pre-registered (Active in Registry)
- **Target Component:** FashXStudio Storefront Embedded Widget (`fashx-widget.js`)
- **Launch Date:** Phase 12 Week 2

---

## 1. Background & Hypothesis

In Path B (Brand-First B2B), shopper engagement begins when a visitor on a partner brand's product display page (PDP) notices and clicks the FashXStudio widget pill.

- **Hypothesis:** Framing the CTA around fit certainty ("See How It Fits") reduces psychological hesitation and body scrutiny anxiety compared to avatar/body framing ("Try On My Body"), yielding a higher modal open rate without degrading downstream try-on completion.

---

## 2. Variants & Traffic Allocation

Deterministic bucketing via `SHA256(shopper_id + salt) % 100`:
- **Variant A (Control - 50%):** `"See How It Fits"`
  - Subtle hanger/ruler icon
  - Clean pill button positioned next to size selector
- **Variant B (Treatment - 50%):** `"Try On My Body"`
  - Mirror/avatar icon
  - Same pill styling and position

---

## 3. Metrics

### Primary Metric
- **Widget Modal Open Rate:** `COUNT(DISTINCT session_id WHERE event = 'widget_modal_opened') / COUNT(DISTINCT session_id WHERE event = 'widget_loaded')`

### Guardrail & Secondary Metrics
- **Photo Upload Conversion:** `widget_photo_uploaded / widget_modal_opened` (must not drop by > 5% relative).
- **Try-On Completion Rate:** `widget_tryon_rendered / widget_modal_opened`.
- **Shopper Bounce Rate:** Session bounce rate on PDP must not increase.
- **Latency / Render Overhead:** Widget initialization script time $< 15\text{ms}$.

---

## 4. Sample Size & Power Calculation

- **Baseline Open Rate:** 4.2% (observed in preliminary partner heatmaps).
- **Minimum Detectable Effect (MDE):** +15% relative (from 4.2% to 4.83%).
- **Statistical Power ($\beta$):** 80% ($\beta = 0.20$).
- **Significance Level ($\alpha$):** 5% (two-sided, $\alpha = 0.05$).
- **Required Sample Size:** ~2,400 distinct widget sessions per arm (4,800 sessions total across participating brand PDPs).
- **Run Duration:** Estimated 7–10 days across initial brand cohort.

---

## 5. Decision Rules

1. **Ship Treatment (Variant B):** If Variant B achieves statistically significant positive improvement ($p < 0.05$) in Modal Open Rate AND does not degrade photo upload rate by $> 5\%$.
2. **Retain Control (Variant A):** If Variant A wins or if difference is not statistically significant after 5,000 sessions.
3. **Emergency Stop (Kill Criteria):** If either variant causes widget crash rate $> 0.1\%$ or PDP page load degradation $> 50\text{ms}$, freeze experiment immediately and fall back to static text.

---

## 6. Privacy & Data Protection Compliance

- Shopper identity is anonymized session tokens; zero biometric data or phone numbers are associated with the experiment exposure record.
- Exposures logged to `experiment_exposures` and mirrored in privacy-safe aggregate view `v_experiment_exposures`.
- Ephemeral session tokens automatically age out after 24 hours.
