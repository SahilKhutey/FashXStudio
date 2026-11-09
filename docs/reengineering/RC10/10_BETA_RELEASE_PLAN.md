# RC10: Beta Release Plan & Gate Evaluation

## 1. Beta Release Gates (B1–B9)
Beta authorization requires explicit, verified satisfaction of all nine gates defined in [`scripts/rc10/beta_gates.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc10/beta_gates.py).

| Gate | Description | Criteria | Current Status |
| :--- | :--- | :--- | :--- |
| **`B1_complete_journey`** | End-to-End User Journey | Discovery → Garment → VTO → Wardrobe → Buy-Click works | **HOLD (Pending Real Cohort)** |
| **`B2_catalog_permissions`** | Catalog Rights & Provenance | 100% of products have verified commercial clearance | **HOLD (Pending Partner Sign-off)** |
| **`B3_recommendation_quality`** | Recommendation Quality | nDCG@10 meets target on judged human dataset | **HOLD (Pending Judged Set)** |
| **`B4_vto_truthfulness`** | VTO Quality & Accuracy | Consented test images verified against real provider | **HOLD (Pending Vendor Live Runs)** |
| **`B5_privacy`** | Privacy & Data Erasure | GDPR/DPDP consent, ownership isolation, erasure | **PASSED (Code/Invariants Verified)** |
| **`B6_reliability`** | System Reliability | API p95 $\le 800\text{ms}$, 5xx $< 0.1\%$, worker retries | **PASSED (Automated CI Verified)** |
| **`B7_mobile_qa`** | Mobile Device QA | Android & iOS physical device smoke journeys | **HOLD (Pending Physical Devices)** |
| **`B8_operations`** | Monitoring & Runbooks | Alert rules, Sentry/Prometheus dashboards active | **HOLD (Pending Staging Infra)** |
| **`B9_legal_review`** | Legal & Retailer Review | Terms of Service, Privacy Policy, affiliate handoff | **HOLD (Pending Founder/Counsel)** |

## 2. Gate Decision Mechanism
```python
from scripts.rc10.beta_gates import evaluate_beta_gates

decision = evaluate_beta_gates(active_gates)
# Returns GateDecision(decision="GO" | "HOLD", passed=..., blocked=..., missing=...)
```
- A `GO` decision is issued **only** when all 9 gates evaluate to `True`.
- Any missing or failed gate defaults to `HOLD`.

## 3. Rollback Procedure
If any critical regression occurs during beta testing:
1. Revert `ReleaseConfig` traffic flags to previous stable deployment.
2. If database rollback is needed, run `alembic downgrade -1` after verifying backup snapshot.
3. Notify active beta participants through app banner or push notice.
