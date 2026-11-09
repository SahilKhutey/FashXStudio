# RC13: Product Validation & Pilot Metrics (M1–M5 Contract)

## 1. Product Validation Goals
Validate the end-to-end user shopping journey across physical test devices and real shoppers:
1. Registration & explicit plain-language DPDP consent.
2. Photo capture & ephemeral upload to private quarantine bucket.
3. Garment discovery & vector-based style recommendations.
4. Virtual try-on execution & visual inspection.
5. Closet saving and lookbook curation.
6. Affiliate handoff (merchant redirect).

## 2. Pre-Registered Metrics Contract (Phase 10 Closed Pilot)
Evaluated directly via [`scripts/rc13/evaluate_product_metrics.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_product_metrics.py):

### Must-Haves (100% Required for "GO")
| Metric Key | Threshold | Description |
|---|---|---|
| `M1_login_invitee_completion_rate` | $\ge 60\%$ | Invitees who log in and complete onboarding with accepted photo |
| `M1_onboarding_starter_completion_rate` | $\ge 80\%$ | Onboarding starters who successfully complete |
| `M2_mean_vto_rating` | $\ge 3.80 / 5.0$ | Average visual try-on rating |
| `M2_ratings_gte_4_rate` | $\ge 70\%$ | Proportion of try-on ratings $\ge 4$ |
| `M2_defect_rate` | $\le 15\%$ | Distinct jobs with unnatural/distortion/drift defect flags |
| `M3_crash_free_sessions` | $\ge 99.0\%$ | Mobile client crash-free session rate |
| `M3_tryon_success_rate` | $\ge 90.0\%$ | End-to-end try-on job completion rate |
| `M3_p95_latency_seconds` | $\le 45.0\text{s}$ | P95 latency (queue wait + GPU inference) |
| `M4_privacy_incident_count` | $\le 0$ | Data exposure, leakage, or unquarantined photo incidents |
| `M4_photo_comfort_agreement_rate` | $\ge 80\%$ | Agreement with photo upload comfort survey question |
| `M4_consent_dropoff_rate` | $\le 10\%$ | Users who abandon during consent screen |
| `M5_week2_return_rate` | $\ge 50\%$ | Activated users returning in Days 7–13 |

### Should-Haves (At Least 3 of 4 Groups Required)
- **Group S1 (Feed Relevance)**: Survey ratings $\ge 4/5 \ge 60\%$, Negative feed signals $\le 15\%$.
- **Group S2 (Engagement)**: Week 1 try-on rate $\ge 60\%$, Median try-ons/user $\ge 3$, Median min to first try-on $\le 10\text{m}$.
- **Group S3 (Purchase Intent)**: "Buy on Store" click rate $\ge 40\%$, Verified purchases reported $\ge 3$.
- **Group S4 (Satisfaction)**: SUS score $\ge 68$, PMF very disappointed rate $\ge 30\%$, NPS $\ge 20$.

## 3. Decision Rules
- **GO**: All 12 must-have metrics PASS, $\ge 3$ should-have groups PASS, 0 hard stop rules triggered.
- **FIX & RE-RUN**: 1 or 2 must-haves missed by narrow margin with identified root cause and concrete fix.
- **PIVOT OR STOP**: M2 (Realism) or M4 (Trust) failed without viable fix, or M5 (Retention) $< 25\%$.
- **HOLD**: Any required must-have metric is unmeasured or missing.
