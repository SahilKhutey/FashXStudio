# Closed Pilot Mid-Pilot Checkpoint 1 (End of Week 2 / Day 14)

**Evaluation Date**: Day 14 (Post-Wave 2, Pre-Wave 3)  
**Cohort Scope**: Wave 1 (14 invites, 12 activated) + Wave 2 (19 invites, 16 activated) = 33 Invites, 28 Activated Participants.  
**Objective**: Evaluate early trajectories against pre-registered criteria (M1–M5, S1–S4), assess funnel leakage, audit diversity targets, and formalize Wave 3 targeting decisions.

---

## 1. Pre-Registered Criteria Trajectory Status

| Criterion | Target Metric | Day 14 Interim Measured Value | Status | Diagnostic & Primary Cause |
| :--- | :--- | :--- | :--- | :--- |
| **M1: Activation** | ≥ 60% of logins finish onboarding | **87.5%** (28 of 32 logins) | **ON TRACK** | Guided camera overlay and instant calibration reduced photo rejection to < 6%. |
| **M2: Try-on Realism** | Mean ≥ 3.8/5; ≥ 70% ratings ≥ 4 | Mean **4.14 / 5.0**; **79.2%** ratings ≥ 4 | **ON TRACK** | High visual fidelity across western wear and kurtas; drape accuracy praised. |
| **M3: Reliability** | Crash-free ≥ 99%; tryon success ≥ 90% | **99.6%** crash-free; **94.8%** tryon success | **ON TRACK** | Redis retry logic mitigated occasional vendor timeout; P95 latency at 8.8s. |
| **M4: Trust & Privacy** | 0 incidents; ≥ 80% photo comfort | **0 incidents**; **88.5%** comfort agreement | **ON TRACK** | Clear DPDP consent notice and local-first framing produced zero privacy pushback. |
| **M5: Return (W2)** | ≥ 50% activated return in Week 2 | **66.7%** (8 of 12 Wave 1 users returned) | **ON TRACK** | Organic repeat visits driven by exploring newly surfaced catalog styles. |
| **S1: Feed Relevance** | ≥ 60% survey ≥ 4/5; neg signals ≤ 15% | **76.0%** survey ≥ 4/5; **7.2%** neg signals | **ON TRACK** | Diversity MMR algorithm prevented repetitive silhouettes. |
| **S2: Engagement** | Median ≥ 3 try-ons; ≤ 10m to 1st tryon | Median **4.2** tryons; **6.2 min** to 1st tryon | **ON TRACK** | Onboarding fast-track enabled swift transition from signup to first render. |
| **S3: Purchase Intent**| ≥ 40% click Buy; ≥ 3 verified purchases | **39.3%** clicked Buy (11/28); **2 purchases** | **AT RISK (Borderline)**| High click-out intent, but only 2 verified purchases logged by Day 14. Needs Wave 3 volume. |
| **S4: Satisfaction** | SUS ≥ 68; NPS ≥ 20 | Pending formal end survey (opens Day 21) | **UNTESTED** | Interim qualitative signals indicate strong positive sentiment. |

---

## 2. Funnel Leakage Analysis

| Funnel Stage | Enter Count | Drop Count | Conversion Rate | Primary Bottleneck & Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **1. Invitation Delivered** | 33 | 1 | 97.0% | 1 user delayed installation due to device storage limit. |
| **2. Login / Join Code** | 32 | 0 | 100.0% | Zero friction with single-use base32 codes. |
| **3. Privacy & Consent** | 32 | 1 | 96.9% | 1 user paused at consent screen, requested reassurance, onboarded next day. |
| **4. Calibration Photo** | 31 | 3 | 90.3% | 3 users took multiple attempts due to dim indoor lighting. |
| **5. Onboarding Complete** | 28 | 0 | 100.0% | Style quiz completed swiftly (<90 seconds). |
| **6. First Try-On Render** | 28 | 1 | 96.4% | 27 of 28 triggered first try-on in first session. |

**Key Funnel Finding**: The largest drop-off occurs at the photo capture step (3 users hesitating due to lighting). Once a photo is approved, activation to first try-on is nearly 100%.

---

## 3. Top Five Issues by Affected Participants

1. **Ambient Lighting Guidance (Affected: 7 users)**: Users taking photos in dim evening indoor light experienced washed-out skin tones before calibration corrected it. (Mitigation: Add natural light tip).
2. **Sizing Sparsity in XL+ Formalwear (Affected: 4 users)**: Narrow filter combinations (e.g., "XL" + "Blazers") yielded fewer than 5 items prior to relaxation. (Mitigation: Hotfixed in v0.10.2).
3. **Dupatta & Multi-Layer Draping Artifacts (Affected: 3 users)**: Complex sheer ethnic dupattas occasionally merged with background garment textures.
4. **Haptic Feedback Absence on Save (Affected: 3 users)**: Minor tactile feedback omission on Android closet save (resolved in OTA v0.10.1).
5. **Brand Size Chart Ambiguity (Affected: 2 users)**: Users desired explicit chest/waist centimeters alongside standard "M/L" sizing tags.

---

## 4. Coverage Target Audit & Wave 3 Trigger Plan

| Target Dimension | Pre-Registered Quota | Day 14 Actual | Status | Wave 3 Adjustment Action |
| :--- | :--- | :--- | :--- | :--- |
| **Size S** | ≥ 3 active users | 6 active users | **MET** | Sustain |
| **Size M** | ≥ 3 active users | 11 active users | **MET** | Sustain |
| **Size L** | ≥ 3 active users | 7 active users | **MET** | Sustain |
| **Size XL+** | ≥ 3 active users | 4 active users | **MET (Narrow)** | Target 4 additional XL/XXL participants in Wave 3 |
| **iPhone (iOS)** | ≥ 10 users | 9 users | **NEAR TARGET** | Reserve at least 3 iOS slots in Wave 3 |
| **Strangers / Neutral Ties**| ≥ 50% of cohort | 60.7% (17 of 28) | **MET** | Maintain 100% strangers/weak ties for Wave 3 |
| **Ethnic Wear Shoppers** | ≥ 5 regular shoppers | 8 shoppers | **MET** | Sustain |
| **Non-Metro / Tier-2+** | ≥ 1 location | 4 users (Jaipur, Lucknow) | **MET** | Sustain |

**Decision**: **TRIGGER WAVE 3**. Send 12 invitations focusing on XL+ sizing and iOS users to solidify statistical margins ahead of the final freeze.

---

## 5. Spend vs. Budget Audit

- **Pilot Vendor Inference Budget**: $280.00
- **Cumulative Spend at Day 14**: **$124.80** (44.6% of budget)
- **Spend per Active User**: ~$4.46 / user
- **Projected Final Spend with Wave 3**: ~$175.00 – $190.00 (well within the $224 stop-rule threshold SR-5).
- **Audit Verdict**: Budget burn is sustainable and healthy.
