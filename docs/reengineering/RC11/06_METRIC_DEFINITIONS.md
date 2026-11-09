# RC11: Metric Definitions & Frozen Denominators

## 1. Frozen Denominator Rules
To prevent misleading conversion claims, denominators are frozen prior to Alpha recruitment:

| Metric | Numerator | Denominator | Invariant |
| :--- | :--- | :--- | :--- |
| **M1: Activation (Login)** | Users completing onboarding with photo | Users who logged in via invite | Observation window: 7 days |
| **M1: Activation (Onboarding)**| Users completing onboarding | Users who started onboarding | Direct funnel drop-off |
| **M2: Realism Mean** | Sum of visual ratings (1–5) | Valid ratings submitted | Minimum 5 ratings |
| **M2: Realism $\ge 4$** | Ratings $\ge 4$ | Valid ratings submitted | Target $\ge 70\%$ |
| **M2: Defect Rate** | Defect tags flagged | Total rated try-on outputs | Target $\le 15\%$ |
| **M3: Crash-Free Sessions**| Sessions with zero unhandled errors | Total instrumented sessions | Target $\ge 99.0\%$ |
| **M3: Try-On Success** | Completed try-on jobs | Submitted try-on jobs | Target $\ge 90.0\%$ |
| **M3: P95 Latency** | P95 total duration (queue + run) | Completed try-on jobs | Target $\le 45\text{ seconds}$ |
| **M4: Photo Comfort** | Survey ratings $\ge 4$ ("comfortable") | Trust survey respondents | Target $\ge 80\%$ |
| **M4: Consent Drop-off** | Users who abandoned consent screen | Total consent screen starters | Target $\le 10\%$ |
| **M5: Week-2 Return** | Activated users returning in Days 7–13| Activated users with 13+ days tenure| **Excludes unexpired windows** |
| **S1: Feed Relevance** | Feed survey answers $\ge 4/5$ | Feed survey respondents | Target $\ge 60\%$ |
| **S1: Negative Signals** | "Hide" or "not interested" clicks | Total viewed feed cards | Target $\le 15\%$ |
| **S2: Week-1 Try-On** | Users with $\ge 1$ try-on in Week 1 | Total activated users | Target $\ge 60\%$ |
| **S3: Purchase Intent** | Users clicking "Buy on Store" | Total activated users | Target $\ge 40\%$ |
| **S3: Verified Purchases** | Manually verified purchase reports | Active pilot participants | Target $\ge 3$ verified |

## 2. Incomplete Observation Windows
- Participants whose 7-day (or 13-day) observation window has not elapsed are excluded from the denominator.
- Incomplete windows must never be recorded as user churn or engagement failure.
