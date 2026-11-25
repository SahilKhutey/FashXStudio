# Result Disclosure & Labeling Specification

> **UX copy, disclaimers, and presentation standards.**

## 1. Approved Terminology
The following terms are standardized across mobile, web, and merchant widget integrations:

| Interface Surface | Required Approved Copy |
|---|---|
| **VTO Result Heading** | `Virtual Try-On` |
| **Image Caption** | `AI-generated visual simulation` |
| **Result Status** | `Visual result generated` |
| **Fit Section Heading** | `Size and fit information` |
| **Missing Fit Data** | `Fit recommendation unavailable` |
| **Core Disclaimer** | `Visual try-on does not verify physical fit` |
| **Action Link** | `View merchant size chart` |

## 2. Prohibited Claims
The following phrases are strictly blacklisted from all VTO outputs and copy:
- `Verified fit` / `Verified physical fit`
- `Perfect fit` / `Guaranteed fit`
- `Your exact body fit`
- `This size will fit you`
- `True-to-size confirmation`
- `Physically accurate fit`
- `Size confirmed by AI`
- `Never get the wrong size again`

## 3. Server-Controlled Policy Enforcement
The backend enforces presentation policy via `get_presentation_policy()` in `backend/fashx/presentation/claims.py`:
```json
{
  "presentation": {
    "result_type": "VISUAL_TRY_ON",
    "is_ai_generated": true,
    "fit_verified": false,
    "fit_prediction_id": null,
    "disclaimer_code": "VISUAL_TRYON_NOT_FIT_VERIFICATION",
    "fit_recommendation_available": false,
    "fit_guaranteed": false,
    "policy_version": "presentation-v1"
  }
}
```
Client applications cannot override `result_type` to `VERIFIED_FIT` or force `fit_verified=True`.
