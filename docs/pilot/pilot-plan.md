# Pre-Registered Closed Pilot Plan (Phase 10)

**Project**: FashXStudio Closed Beta / Pilot  
**Target Window**: October – November 2026 (3–4 weeks execution)  
**Sample Target**: 40–50 Activated Users (from 60–70 Invitations)  
**Status**: **PRE-REGISTERED & FROZEN** (Committed prior to Alpha launch)  
**Prerequisite Gate**: Gate G1, G3, G4, G5 Cleared; `v0.9-pilot-ready` Signed.  

---

## 1. Sample & Cohort Structure

| Cohort | Target Size | Primary Purpose | Duration |
| :--- | :--- | :--- | :--- |
| **Alpha** | 5 (Trusted & blunt) | Uncover launch blockers, rehearse support, deletion, and kill switches | 3 days |
| **Wave 1** | 12–15 | First real empirical telemetry, fix top UI/flow friction points | Week 1 |
| **Wave 2** | 15–20 | Validate fixes from Wave 1, broaden participant mix | Week 2 |
| **Wave 3 (Optional)** | 10–15 | Top-up cohort if any coverage targets (size/phone/style) are missed | Week 3 |

### Coverage Targets (Mandatory Diversity Slices)
- **Size Coverage**: At least 3 active participants each in **S**, **M**, **L**, and **XL-and-above** (testing catalog size distribution).
- **Mobile Platforms**: Android majority, plus at least **10 iPhone users** (validating iOS cross-platform parity).
- **Recruitment Relationship**: At least **50% of participants** must have **no personal tie** to the founding team (neutral strangers/weak ties to eliminate friendliness bias).
- **Garment Category**: At least **5 participants** who regularly shop for **ethnic wear** (validating kurtas, dupattas, and sarees).
- **Geographic Representation**: Multiple cities represented, including at least one **non-metro / tier-2+** location.

---

## 2. Core Hypotheses

1. **H1 (Realism & Re-use)**: Users who experience a believable virtual try-on of a real, buyable catalog item on their own body silhouette will return to use the styling tool repeatedly.
2. **H2 (Personalized Feed Relevance)**: A discovery feed driven by size, budget, and a concise style quiz feels sufficiently relevant to drive weekly retention without infinite scroll fatigue.
3. **H3 (Guided Photo Trust)**: When privacy commitments are transparent, consent is explicit, and capture is guided, users will willingly upload a full-body self-portrait.
4. **H4 (Commercial Purchase Intent)**: A meaningful proportion of users exploring personalized outfits will click through ("Buy on Store") to partner merchants for items discovered in the app.

---

## 3. Success Criteria & Release Gate G6

### Must-Haves (All 5 Required for "GO")

| # | Criterion | Metric & Measurement Definition | Minimum Threshold |
| :--- | :--- | :--- | :--- |
| **M1** | **Activation** | Share of invitees who log in and finish onboarding with an accepted body photo within 7 days; and share of those who start onboarding who complete it. | **≥ 60%** of login invitees;<br>**≥ 80%** of onboarding starters |
| **M2** | **Try-on Realism** | In-app visual rating on 1–5 scale; proportion of ratings ≥ 4; rate of "face changed" or "looks unnatural" defect tags. | **Mean ≥ 3.8 / 5.0**;<br>**≥ 70%** ratings ≥ 4;<br>**≤ 15%** defect flags |
| **M3** | **Reliability** | Crash-free mobile sessions; user-visible try-on completion rate; P95 end-to-end latency (queue + inference). | **≥ 99.0%** crash-free;<br>**≥ 90.0%** try-on success;<br>**P95 ≤ 45 seconds** |
| **M4** | **Trust & Privacy** | Security / privacy incidents; survey agreement with *"I felt comfortable uploading my photo"*; consent screen abandonment rate. | **0 incidents**;<br>**≥ 80%** agreement;<br>**≤ 10%** consent drop-off |
| **M5** | **Return (Retention)** | Proportion of activated users who return and open the app during their second week (Days 7–13). | **≥ 50%** week-2 return |

### Should-Haves (At least 3 of 4 Required for Clean "GO")

| # | Criterion | Metric & Measurement Definition | Minimum Threshold |
| :--- | :--- | :--- | :--- |
| **S1** | **Feed Relevance** | Survey rating of feed recommendations; hide or "not interested" signal rate on viewed feed cards. | **≥ 60%** survey answers ≥ 4/5;<br>**≤ 15%** negative signals |
| **S2** | **Engagement** | Share completing a try-on in Week 1; median try-ons per activated user; median time from signup to first try-on result. | **≥ 60%** try in Week 1;<br>**Median ≥ 3** try-ons / user;<br>**Median ≤ 10 min** to first try-on |
| **S3** | **Purchase Intent** | Proportion of activated users clicking "Buy on Store" at least once; reported purchases of discovered garments. | **≥ 40%** click Buy;<br>**≥ 3 verified purchases** reported |
| **S4** | **Satisfaction** | System Usability Scale (SUS) score; Sean Ellis PMF question (*"very disappointed if no longer available"*); Net Promoter Score (NPS). | **SUS ≥ 68**;<br>**≥ 30%** very disappointed;<br>**NPS ≥ 20** |

### Decision Rules:
- **GO**: All 5 must-haves met, at least 3 of 4 should-haves met, and 0 stop rules triggered.
- **FIX & RE-RUN**: 1 or 2 must-haves missed by a narrow margin with an identified root cause and concrete fix. Re-run a focused 2-week pilot with new participants.
- **PIVOT OR STOP**: M2 (Realism) or M4 (Trust) failed without viable fix, or Week-2 return (M5) < 25%, or participants consistently reject core value proposition.

---

## 4. Hard Stop Rules (Pause Invites & Intervene Immediately)

| Trigger Event | Immediate Containment Action |
| :--- | :--- |
| **1. Suspected Data Exposure** | Toggle `tryon_enabled = False`, pause all invitations, initiate breach runbook (`breach-response.md`) with 6-hour CERT-In clock. |
| **2. Stability Crash Spike** | Crash-free sessions drop below **98.0%** over a 3-day window. Pause invites, triage stack traces, deploy patch build. |
| **3. Try-On Outage Spike** | User-visible try-on failure exceeds **25.0%** across 30 consecutive jobs. Pause invites, inspect vendor circuit breaker & Redis queue. |
| **4. API 5xx Error Wave** | Global HTTP 5xx error rate exceeds **2.0%** for a full day. Pause invites, initiate SEV-1 incident process. |
| **5. Spend Budget Breach** | Cumulative try-on vendor spend exceeds **80% of pilot budget ($280)** prior to Wave 3. Freeze Wave 3 and audit per-user quotas. |
| **6. Privacy Discomfort Attrition** | 3 or more participants withdraw from the pilot citing privacy discomfort or lack of trust. Pause, review consent and capture guidance. |
| **7. Offensive AI Output** | Systemic offensive, inappropriate, or distorted generation reported. Disable affected category via capability gate, contact user, log incident. |

---

## 5. Change Control Policy

- Bug fixes and stability patches may be deployed freely, but every release must be logged in [`docs/pilot/change-log.md`](./change-log.md).
- **Prohibited during Weeks 2–3**: No modifications to ranker weights, MMR diversity parameters, taste vectors, or onboarding flow steps, preserving statistical interpretability across cohorts.
- All analytics events carry `app_version` and all feed impressions log `ranker_version` to enable segmented analysis.
