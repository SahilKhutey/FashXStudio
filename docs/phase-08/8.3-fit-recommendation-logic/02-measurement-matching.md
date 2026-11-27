# 02 — Measurement Matching Rules

## Measurement Basis Separation

1. **`MeasurementBasis.BODY`**: Merchant chart states target body measurements (`L_{m,s} <= B_m <= U_{m,s}`). Shopper body measurements are compared inclusively using `Decimal` without pre-rounding (`measurement_matches`).
2. **`MeasurementBasis.GARMENT`**: Merchant chart states finished physical garment dimensions. Comparing finished garment dimensions directly as body range matches raises `ValueError` in `measurement_matches`. Evaluating `GARMENT` charts requires explicit validated `EaseRule` entries (`evaluate_ease`, `E = G - B`).
3. **`MeasurementBasis.UNKNOWN`**: Blocked unconditionally by `validate_evidence`.

## Unit & Precision Invariants

- All linear shopper inputs and chart dimensions are normalized to `CM` (`Decimal`) prior to matching while retaining `original_value` and `original_unit`.
- Point measurements (`min == max`) vs bounded ranges (`min <= max`) are supported identically; inverted ranges (`min > max`) fail with `ValueError` / `CONFLICTING_DATA`.
- Incompatible definitions (such as `CHEST` body circumference vs `HALF_CHEST_WIDTH`) are rejected before arithmetic comparison.
