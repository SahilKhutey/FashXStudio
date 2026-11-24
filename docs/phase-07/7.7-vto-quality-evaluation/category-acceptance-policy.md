# Category Acceptance Policy & Quality Gates

## 1. Acceptance Thresholds

For a garment category to transition from `EVALUATING` to `APPROVED_LIMITED`, it must satisfy all 10 deterministic gates:

| Gate | Acceptance Standard | Failure Consequence |
|---|---|---|
| **Sample Size** | $\ge 30$ Distinct Image Pairs | Status remains `EVALUATING` |
| **Job Success Rate** | $\ge 90.0\%$ | Gate fails; status set to `NEEDS_IMPROVEMENT` |
| **Garment Preservation** | $\ge 3.8 / 5.0$ | Gate fails; status set to `NEEDS_IMPROVEMENT` |
| **Body Alignment** | $\ge 3.8 / 5.0$ | Gate fails; status set to `NEEDS_IMPROVEMENT` |
| **Artifact Quality** | $\ge 3.8 / 5.0$ | Gate fails; status set to `NEEDS_IMPROVEMENT` |
| **Identity Preservation** | $\ge 4.0 / 5.0$ | Gate fails; status set to `NEEDS_IMPROVEMENT` |
| **Visual Plausibility** | $\ge 3.8 / 5.0$ | Gate fails; status set to `NEEDS_IMPROVEMENT` |
| **Non-Misleading Score** | $\ge 4.0 / 5.0$ | Gate fails; status set to `NEEDS_IMPROVEMENT` |
| **Reviewer Rejection Rate**| $\le 5.0\%$ | Gate fails; status set to `NEEDS_IMPROVEMENT` |
| **Critical Misleading Count**| **0** (Zero Tolerance) | **Immediate Hard Stop**: Category status set to `BLOCKED` |

---

## 2. Hard Stop Isolation

High scores in one category cannot compensate for failures in another. Even if T-shirts achieve a 4.8/5.0 rating, sarees with distorted pleats or altered models will be blocked independently.
