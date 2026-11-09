# RC13: VTO Quality, Provider & Latency Evaluation

## 1. Inference Engine Criteria
- **Provider Reality**: Real GPU provider (e.g. cloud GPU worker, dedicated inference endpoint) must be verified. Mock and synthetic inference providers are strictly prohibited for production validation.
- **Latency Standards**:
  - P50 target: <= 15.0 seconds.
  - P95 threshold: <= 30.0 seconds.
- **Completion Rate**: >= 95% of submitted try-on jobs must complete successfully.

## 2. Visual Defect Analysis & Deduplication Invariant
Defects are classified across five tags:
1. `artifacts_detected`: visual glitches, floating pixels, warped textures.
2. `body_distortion`: limb stretching, unnatural proportions, posture corruption.
3. `garment_mismatch`: neckline misalignment, sleeve distortion, incorrect fit mapping.
4. `identity_drift`: facial alteration, skin-tone alteration, head distortion.
5. `blur_defect`: loss of garment fabric detail or focal blur.

**Deduplication Rule**:
A single job exhibiting multiple defect tags (e.g. artifacts AND distortion) is counted as **one** defective job. Defect rate is calculated as:
$$\text{defect\_job\_rate} = \frac{\text{distinct defective completed jobs}}{\text{total completed jobs}}$$
The threshold requires $\text{defect\_job\_rate} \le 15.0\%$.

## 3. Evaluation Script
Evaluated by [`scripts/rc13/evaluate_vto.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_vto.py).
