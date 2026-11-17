# Profile Unit Normalization and Precision Rules

## 1. Storage Standards
The FashXStudio database standardizes all physical dimensions in metric units:
- **Height**: Centimeters (`cm`), stored as `NUMERIC(5, 1)`.
- **Weight**: Kilograms (`kg`), stored as `NUMERIC(5, 1)`.

No non-metric units (inches, feet, pounds, stones) are ever stored in the database.

## 2. Normalization Formulas and Implementation

### 2.1 Inches to Centimeters
$$ \text{cm} = \text{inches} \times 2.54 $$
- **Rounding Mode**: `ROUND_HALF_UP` to 1 decimal place (`0.1`).
- **Validation**: `inches > 0`.

### 2.2 Feet and Inches to Centimeters
$$ \text{total\_inches} = (\text{feet} \times 12) + \text{inches} $$
$$ \text{cm} = \text{total\_inches} \times 2.54 $$
- **Rounding Mode**: `ROUND_HALF_UP` to 1 decimal place (`0.1`).
- **Validation**: `feet >= 0`, `0 <= inches < 12`, `total_inches > 0`.

### 2.3 Pounds (lb) to Kilograms (kg)
$$ \text{kg} = \text{pounds} \times 0.45359237 $$
- **Rounding Mode**: `ROUND_HALF_UP` to 1 decimal place (`0.1`).
- **Validation**: `pounds > 0`.

## 3. Decimal Precision Guarantee
All conversions in `backend/fashx/profile/units.py` use Python's standard `decimal.Decimal` library to eliminate binary floating-point representation drift (e.g. `177.79999999999998` instead of `177.8`).
