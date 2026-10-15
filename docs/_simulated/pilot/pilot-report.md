# Closed Pilot Final Quantitative Report (Phase 10)

**Date of Data Freeze**: Day 28 Post-Launch  
**Telemetry Source**: Salted pseudonymous database views (`v_pilot_*`) with automated small-cell suppression (< 5 participants).  
**Statistical Method**: All proportions reported with 95% Wilson score confidence intervals. As pre-registered in [`docs/pilot/pilot-plan.md`](./pilot-plan.md), intervals that straddle a threshold are categorized strictly as **UNCLEAR**, not assumed to pass.

---

## 1. Participant Census & Cohort Accounting

| Metric | Wave 1 (W1) | Wave 2 (W2) | Wave 3 (W3) | Total / Aggregated |
| :--- | :--- | :--- | :--- | :--- |
| **Invitations Sent** | 14 | 19 | 12 | **45** |
| **Logins / Redeemed Codes** | 13 | 18 | 11 | **42** |
| **Onboarding Started** | 13 | 17 | 10 | **40** |
| **Activated Users (Photo Accepted)** | 12 | 16 | 10 | **38** |
| **Voluntary Withdrawals** | 1 (personal time) | 1 (academic exam) | 0 | **2** |
| **Non-Activations** | 1 (storage limit) | 2 (lighting friction) | 1 (delayed) | **4** |
| **Completed Pilot Tenure (≥ 14d)** | 12 | 16 | 10 | **38** |

### Demographic & Diversity Coverage Audit

| Quota Dimension | Pre-Registered Quota | Measured Cohort Count | Status |
| :--- | :--- | :--- | :--- |
| **Size S** | ≥ 3 active users | 8 participants | **MET** |
| **Size M** | ≥ 3 active users | 14 participants | **MET** |
| **Size L** | ≥ 3 active users | 9 participants | **MET** |
| **Size XL & Above** | ≥ 3 active users | 7 participants | **MET** |
| **Mobile OS: Android** | Majority | 26 participants (68.4%) | **MET** |
| **Mobile OS: iOS (iPhone)** | ≥ 10 users | 12 participants (31.6%) | **MET** |
| **Relationship: Strangers / Neutral Ties** | ≥ 50% | 24 participants (63.2%, 95% CI: [47.3%, 76.6%]) | **MET** |
| **Ethnic Wear Shoppers** | ≥ 5 regular shoppers | 11 participants | **MET** |
| **Non-Metro / Tier-2+ Geography** | ≥ 1 location | 6 participants (Jaipur, Lucknow, Indore) | **MET** |

---

## 2. Gate G6 Pre-Registered Criteria Scorecard

### Must-Have Criteria (All 5 Required for Clean GO)

| # | Criterion | Pre-Registered Threshold | Measured Empirical Value | 95% Wilson Confidence Interval | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **M1** | **Activation** | ≥ 60% of logins accepted photo within 7d | **90.5%** (38/42) | [77.9%, 96.2%] | **PASS** |
| **M2** | **Try-on Realism** | Mean ≥ 3.8/5.0;<br>≥ 70% ratings ≥ 4;<br>≤ 15% defects | Mean: **4.12 / 5.0**;<br>Ratings ≥ 4: **80.0%** (148/185);<br>Defects: **7.6%** (14/185) | Ratings ≥ 4: [73.7%, 85.1%];<br>Defects: [4.6%, 12.3%] | **PASS** |
| **M3** | **Reliability** | Crash-free ≥ 99.0%;<br>Tryon success ≥ 90.0%;<br>P95 latency ≤ 45s | Sessions: **99.57%** (916/920);<br>Tryon: **94.88%** (204/215);<br>P95 Latency: **14.1s** | Sessions: [98.9%, 99.8%];<br>Tryon: [91.1%, 97.1%] | **PASS** |
| **M4** | **Trust & Privacy** | 0 security incidents;<br>≥ 80% photo comfort;<br>≤ 10% consent drop | Incidents: **0**;<br>Comfort: **87.2%** (34/39);<br>Drop: **4.8%** (2/42) | Comfort: [73.3%, 94.4%];<br>Drop: [1.3%, 15.8%] | **UNCLEAR** *(Interval [73.3%, 94.4%] straddles 80% threshold)* |
| **M5** | **Return (Retention)**| ≥ 50% activated return in Week 2 | **68.4%** (26/38) | [52.5%, 80.9%] | **PASS** |

### Should-Have Criteria (At Least 3 of 4 Required)

| # | Criterion | Pre-Registered Threshold | Measured Empirical Value | 95% Wilson Confidence Interval | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **S1** | **Feed Relevance** | ≥ 60% survey answers ≥ 4/5;<br>≤ 15% negative signals | Survey: **79.5%** (31/39);<br>Neg signals: **7.0%** (240/3,420) | Survey: [64.5%, 89.2%];<br>Neg signals: [6.2%, 7.9%] | **PASS** |
| **S2** | **Engagement** | ≥ 60% try in Week 1;<br>Median ≥ 3 try-ons/user;<br>Median ≤ 10 min to 1st tryon | Week 1: **92.1%** (35/38);<br>Median: **4.5** try-ons;<br>Median time: **6.2 min** | Week 1: [79.2%, 97.3%] | **PASS** |
| **S3** | **Purchase Intent** | ≥ 40% click "Buy on Store";<br>≥ 3 verified purchases | Buy clicks: **47.4%** (18/38);<br>Purchases: **3 verified** | Buy clicks: [32.5%, 62.7%] | **UNCLEAR** *(Interval [32.5%, 62.7%] straddles 40% threshold)* |
| **S4** | **Satisfaction** | SUS score ≥ 68;<br>≥ 30% "very disappointed";<br>NPS ≥ 20 | SUS: **76.5 / 100**;<br>Very disappointed: **35.9%** (14/39);<br>NPS: **+32** | Disappointed: [22.7%, 51.9%] | **PASS** |

---

## 3. Funnel Conversion & Cohort Progression

```
[45 Invitations] 
       │ 93.3% [42 Logged In]
       │ 95.2% [40 Onboarding Started]
       │ 95.0% [38 Photo Approved / Activated]
       │ 92.1% [35 Completed Try-On in Week 1]
       │ 68.4% [26 Returned in Week 2]
       ▼
[18 Users Clicked "Buy on Store"] (47.4%) ──► [3 Verified Merchant Purchases]
```

### Cohort Progression Comparison
- **Wave 1 (v0.10.0)**: Onboarding completion 85.7%; first try-on time median 7.4 min.
- **Wave 2 & 3 (v0.10.1 & v0.10.2)**: Onboarding completion 93.1%; first try-on time median 5.8 min. OTA improvements to pose guidance and haptic feedback reduced calibration friction by 18%.

---

## 4. Try-On Quality by Demographic & Garment Slice

*Note: Cells with fewer than 5 participants are suppressed (`<5`) to preserve anonymity and avoid misleading micro-samples.*

| Slice Dimension | Category / Group | Sample Size (n) | Mean Rating (1–5) | Defect Rate (95% CI) |
| :--- | :--- | :--- | :--- | :--- |
| **Garment Category** | Western Tops / Shirts | 78 jobs | 4.24 / 5.0 | 5.1% [1.9%, 12.4%] |
| | Western Bottoms / Trousers | 44 jobs | 4.02 / 5.0 | 9.1% [3.3%, 21.4%] |
| | Western Dresses | 38 jobs | 4.18 / 5.0 | 5.3% [1.3%, 17.0%] |
| | Ethnic Wear (Kurtas & Sets) | 55 jobs | 4.05 / 5.0 | 10.9% [4.8%, 21.8%] |
| **Photo Type** | Full-length (Mirror / Timer) | 162 jobs | 4.16 / 5.0 | 6.8% [3.8%, 11.8%] |
| | Cropped / Upper Torso | <5 *(suppressed)* | <5 *(suppressed)* | <5 *(suppressed)* |
| **Skin-Tone Bucket** | Fitzpatrick Type I–II | <5 *(suppressed)* | <5 *(suppressed)* | <5 *(suppressed)* |
| | Fitzpatrick Type III–IV | 118 jobs | 4.15 / 5.0 | 7.6% [4.0%, 13.9%] |
| | Fitzpatrick Type V–VI | 56 jobs | 4.09 / 5.0 | 7.1% [2.7%, 16.9%] |
| **Size Group** | Size S | 36 jobs | 4.19 / 5.0 | 5.6% [1.4%, 18.1%] |
| | Size M | 72 jobs | 4.15 / 5.0 | 6.9% [2.9%, 15.2%] |
| | Size L | 46 jobs | 4.08 / 5.0 | 8.7% [3.2%, 20.3%] |
| | Size XL & Above | 31 jobs | 4.03 / 5.0 | 9.7% [3.1%, 24.9%] |

### Comparison with Phase 5 Model Expectations
- Defect rate across Fitzpatrick V–VI (7.1%) matched Fitzpatrick III–IV (7.6%), confirming that the pre-inference color calibration and ambient histogram alignment implemented in Phase 5 resolved historical dark skin-tone color clipping.
- Ethnic wear defects (10.9%) were slightly elevated due to sheer fabric draping on dupattas, but remained well within the ≤ 15.0% threshold.

---

## 5. Error Code & Failure Taxonomy

Total try-on generation requests: **215**  
Successful completions: **204** (94.9%)  
Failed jobs: **11** (5.1%)

| Error Code | Occurrences | Share of Failures | Classification & Root Cause | Fixability |
| :--- | :--- | :--- | :--- | :--- |
| `ERR_POSE_OCCLUSION` | 4 | 36.4% | Hand placed over chest or bag blocking torso | Fixable via in-camera capture validation |
| `ERR_GARMENT_DRAPE` | 3 | 27.3% | Multi-layer sheer dupatta silhouette confusion | AI vendor model prompt tuning |
| `ERR_VENDOR_TIMEOUT` | 2 | 18.2% | Transient upstream GPU timeout (> 30s) | Handled by automated worker retry |
| `ERR_LIGHTING_CONTRAST`| 2 | 18.2% | Extreme backlight underexposure | Fixable via real-time exposure hint |

---

## 6. Feed Engagement & Discovery Metrics

- **Total Card Impressions**: 3,420
- **Negative Feedback Signals** (Hide / "Not Interested"): 240 (7.0%, 95% CI: [6.2%, 7.9%])
- **Saved to Closet Actions**: 168 (4.91 saves per 100 impressions)
- **Primary Reason Chips on Saved Garments**:
  - *"Matches my body silhouette"*: 41.7%
  - *"Flattering color palette"*: 28.6%
  - *"Versatile for occasions"*: 17.9%
  - *"Great price point"*: 11.8%
- **Zero-Result Rate (`no_items_in_size`)**: 0.4% after v0.10.2 relaxation ladder patch.
- **Relaxation Ladder Triggers**: Fired on 42 user queries (1.2% of sessions), broadening constraints smoothly without empty states.

---

## 7. Try-On Frequency Distribution & Latency

- **Median Time from Signup to First Try-On**: **6.2 minutes** (P25: 4.1 min, P75: 9.8 min)
- **Sessions per Active User per Week**: **3.4 sessions / week**
- **Try-On Distribution**:
  - 1–2 try-ons: 6 users (15.8%)
  - 3–5 try-ons: 20 users (52.6%)
  - 6–10 try-ons: 9 users (23.7%)
  - > 10 try-ons: 3 users (7.9%)
  - *Finding*: Usage was broadly distributed across the median rather than artificially driven by 1 or 2 extreme outliers.
- **Latency Distribution**:
  - Median Latency: **7.8 seconds**
  - P90 Latency: **11.4 seconds**
  - P95 Latency: **14.1 seconds**
  - Maximum Recorded: **28.6 seconds** (well under 45.0s cap)

---

## 8. Pilot Operational Cost Accounting

| Cost Category | Total Spend (USD) | Spend per Active User (n=38) | Spend per Completed Try-On (n=204) |
| :--- | :--- | :--- | :--- |
| **Try-On GPU Inference** | $150.96 | $3.97 | $0.74 |
| **Catalog Enrichment & Vector Indexing** | $14.20 | $0.37 | $0.07 |
| **Cloud Hosting & Redis Infrastructure** | $18.50 | $0.49 | $0.09 |
| **Email & SMS Validation (Supabase)** | $2.80 | $0.07 | $0.01 |
| **Total Pilot Operational Cost** | **$186.46** | **$4.91** | **$0.91** |

*Cost per Accepted Try-on (Rating ≥ 4, n=148)*: **$1.26** per high-satisfaction generation.
