# 04 — Unit Normalization

## 1. Normalization Invariants

Size measurements must be comparable, deterministic, and free of floating-point rounding errors.

### Core Invariants
1. **Canonical Storage in Centimeters**: All measurement values are stored internally in centimeters (`CM`) alongside the merchant's original value and unit.
2. **Fixed-Point Decimal Arithmetic**: Calculations use Python's `Decimal` type to avoid IEEE 754 floating-point inaccuracies.
3. **Round Half-Up Precision**: Conversion values are quantized to two decimal places (`0.01`) using `ROUND_HALF_UP`.
4. **Finite, Strictly Positive Validation**: Values must be strictly greater than zero, non-infinite, and non-NaN.

## 2. Conversion Formulae

$$\text{value}_{\text{cm}} = \begin{cases} 
\text{value} \times 2.54 & \text{if unit} \in \{\text{INCH}, \text{IN}\} \\
\text{value} \div 10.0 & \text{if unit} = \text{MM} \\
\text{value} & \text{if unit} = \text{CM}
\end{cases}$$

Reverse conversion to display unit:

$$\text{value}_{\text{in}} = \text{quantize}\left(\frac{\text{value}_{\text{cm}}}{2.54}, 0.01\right)$$

## 3. Validation Against Extremes
Before normalization, incoming measurements are verified against the minimum and maximum boundaries defined in the field registry. Values outside plausible human apparel dimensions (e.g., a 5 cm waist or a 500 cm chest) are rejected immediately.
