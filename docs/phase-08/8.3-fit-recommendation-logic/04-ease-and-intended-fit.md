# 04 — Ease & Intended Fit Policy

## Rule Principle

Calculated ease $E = G - B$ is treated as product-level garment construction evidence, not a free parameter guessed from a shopper's subjective `FitPreference`.

## `EaseRule` Governance (`ease_policy.py`)

Every `EaseRule` specifies:
- `category`, `measurement`, `basis` (`MeasurementBasis.GARMENT`)
- `intended_fit` (`SLIM`, `REGULAR`, `RELAXED`, `OVERSIZED`, `NO_PREFERENCE`)
- `garment_construction`, `minimum_cm`, `maximum_cm`
- `policy_version`, `evidence_reference` (mandatory non-empty audit reference)

`DEFAULT_EASE_REGISTRY` ships empty (`approved_rules=[]`). When a merchant chart uses `GARMENT` basis and no approved `EaseRule` applies, `validate_evidence` blocks with `EASE_POLICY_MISSING` / `FIT_POLICY_MISSING`. When a valid `BODY` recommendation is produced for a shopper with a preference other than `NO_PREFERENCE` and no garment ease evidence was evaluated, reason code `PREFERENCE_NOT_EVALUATED` is emitted transparently.
