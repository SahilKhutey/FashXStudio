# RC07 — Grounded Explanations & Reason Chips Policy

## 1. Objective
Ensure that all reason chips and stylist explanations presented in the mobile feed are strictly grounded in verified garment metadata, user preferences, and real scores.

## 2. Hard Policy: No Speculative Fit Claims
Coding agents and recommendation pipelines are strictly prohibited from generating unverified or hallucinated fit claims:
- **Prohibited**: "Fits your exact waist measurement", "Guaranteed tailored fit", "Fits true to size" (unless backed by real user body measurement comparison).
- **Approved**: "In Your Size", "Within Budget", "Style Match", "Color Harmony", "Try-On Ready", "Fresh Arrival", "Top Pick".

## 3. Reason Chips Taxonomy
- **Module**: `backend/fashx/discovery/explanations.py`
| Chip | Condition |
|---|---|
| `"Top Pick"` | `final_score >= 0.85` |
| `"Visual Taste Match"` | `semantic_score >= 0.60` (measured against real taste vector) |
| `"Style Match"` | `style_score >= 0.80` |
| `"{Color} Harmony"` | `color_score >= 0.80` and `dominant_color` present |
| `"In Your Size"` | `size_score >= 0.99` |
| `"Within Budget"` | `budget_score >= 0.90` |
| `"Try-On Ready"` | `tryon_supported is True` |
| Fallback | Category or dominant color name |

## 4. Stylist Natural Language Explanations
Explanations are constructed deterministically:
`"Curated garment aligned with your preferred {styles} aesthetic, features flattering {color} tones, supports instant AI virtual try-on."`

## 5. Verification
Unit test `tests/unit/test_rc07_explanations.py` verifies:
- Generation of grounded chips.
- Total absence of unmeasured fit assertions.
- Safe fallback when scores are below thresholds.
