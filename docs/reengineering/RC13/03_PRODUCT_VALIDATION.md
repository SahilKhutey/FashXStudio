# RC13: Product Validation & Pilot Metrics (M1–M5)

## 1. Product Validation Goals
Validate the complete end-to-end user shopping journey:
1. User registration & explicit photo consent.
2. Photo capture & ephemeral upload.
3. Garment discovery & personalized recommendations.
4. Virtual try-on execution & visual inspection.
5. Saving to wardrobe / lookbook.
6. Affiliate handoff (merchant redirect).

## 2. Pre-Registered Metrics (M1–M5)
Per [`docs/pilot/pilot-plan.md`](file:///c:/Users/ASUS/Documents/FashXStudio/docs/pilot/pilot-plan.md):
- **M1 (Activation / Login Rate)**: >= 70% of invited participants log in and complete profile setup.
- **M2 (Try-On Completion Rate)**: >= 60% of activated participants complete at least one virtual try-on.
- **M3 (VTO User Rating)**: Mean user satisfaction rating >= 3.50 out of 5.0 (or >= 75% acceptable rating).
- **M4 (Session Stability)**: >= 99% crash-free sessions across physical pilot test devices.
- **M5 (Privacy & Security)**: Exactly 0 privacy incidents, 0 biometric data leaks, and 0 photo exposure events.

## 3. Evaluator Implementation
Automated validation is implemented in [`scripts/rc13/evaluate_product_metrics.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_product_metrics.py).
Missing metrics evaluate to `UNKNOWN` and fail-closed to `HOLD`.
