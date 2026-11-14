# RC13: VTO Quality, Provider & Latency Evaluation

## 1. Inference Engine Criteria & Real Provider Requirement
- **Provider Reality**: Real commercial GPU inference endpoint must be connected. Mock and synthetic inference providers are strictly prohibited for production evaluation.
- **Latency & Reliability Standards**:
  - **Contractual Release Gate Ceiling**:
    - Completion rate: $\ge 90.0\%$ (per `docs/pilot/pilot-plan.md` M3).
    - P95 end-to-end latency: $\le 45.0$ seconds (per `docs/pilot/pilot-plan.md` M3 and `docs/release/gates.md` G5).
    - Defect job rate: $\le 15.0\%$ (per `docs/pilot/pilot-plan.md` M2).
    - Mean rating: $\ge 3.80 / 5.0$ (per `docs/pilot/pilot-plan.md` M2).
  - **Internal Operational Excellence Targets**:
    - Completion rate: $\ge 95.0\%$.
    - P95 latency: $\le 30.0$ seconds.
    - Defect job rate: $\le 10.0\%$.
    - Mean rating: $\ge 4.00 / 5.0$.

## 2. Visual Defect Analysis & Deduplication Invariant
Defects are classified across five distinct tags:
1. `artifacts_detected`: visual glitches, floating pixels, warped textures.
2. `body_distortion`: limb stretching, unnatural proportions, posture corruption.
3. `garment_mismatch`: neckline misalignment, sleeve distortion, incorrect fit mapping.
4. `identity_drift`: facial alteration, skin-tone alteration, head distortion.
5. `blur_defect`: loss of garment fabric detail or focal blur.

**Strict Deduplication Invariant**:
A single job exhibiting multiple defect tags (e.g. artifacts AND distortion) is counted as **one** defective job:
$$\text{defect\_job\_rate} = \frac{\sum [1 \text{ if any defect tags present}]}{\text{total completed jobs}} \le 15.0\%$$

## 3. Evaluation Script
Evaluated by [`scripts/rc13/evaluate_vto.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_vto.py).
Evaluates both gate ceiling compliance and operational target achievement.
