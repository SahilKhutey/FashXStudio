# 05 — Unit Normalization

## 1. Unit Policy (`backend/fashx/profile/units.py`)

- **Linear & Circumference Fields**: Accept `CM`, `IN`, `MM`; normalized canonically to `CM`.
- **Weight (`WEIGHT`, optional contextual)**: Accepts `KG`; normalized canonically to `KG`.
- Type mismatches (such as `KG` for `CHEST` or `CM` for `WEIGHT`) raise `ValueError` and return HTTP 422.
- All arithmetic uses fixed-point `Decimal` with `ROUND_HALF_UP` to `0.01` precision:
  - `CM = value`
  - `CM = value / 10` for `MM`
  - `CM = value * 2.54` for `IN`
- Original shopper value and unit remain stored cleanly alongside the normalized canonical value to prevent double-conversion across edits.
