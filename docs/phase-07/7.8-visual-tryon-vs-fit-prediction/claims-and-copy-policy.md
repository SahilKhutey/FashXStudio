# Claims & Content Policy

> **Policy enforcement for marketing copy, UI labels, and merchant widget branding.**

## 1. Policy Overview
To protect consumer trust and comply with advertising standards (such as ASCI and FTC guidelines regarding AI assertions), FashXStudio strictly distinguishes between:
1. Demonstrative visual simulations (`VISUAL_SIMULATION`).
2. Verified merchant product dimensions (`SIZE_CHART`).
3. Evidence-based estimation (`FIT_RECOMMENDATION`).

## 2. Centralized Text Validation
The engine `backend/fashx/presentation/claims.py` provides `validate_claim_text(text: str) -> bool`.
Any copy attempting to assert guaranteed fit, perfect fit, or AI confirmed sizing is intercepted and rejected with `ValueError`.

## 3. Comparison of Marketing Claims

| Prohibited Copy | Required Approved Replacement |
|---|---|
| `Find your perfect fit with AI` | `Preview how a garment might look on you` |
| `Know your exact size instantly` | `Explore size guidance where verified data is available` |
| `Guaranteed fit before purchase` | `Visual try-on plus separate size information` |
| `Never get the wrong size again` | `Make more informed apparel decisions` |
| `AI confirms this garment fits` | `Review the merchant chart and available fit guidance` |

## 4. Merchant Widget Restrictions
B2B merchant storefront widgets inherit this policy:
- Merchants may style buttons, fonts, and container backgrounds.
- Merchants **cannot** hide or suppress the visual try-on disclaimer (`show_disclaimer=True` is locked).
- Merchants **cannot** re-label the output as "Verified Fit" or "Guaranteed Size".
