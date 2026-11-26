# 06 — Measurement Validation Rules

## 1. Validation Tiers (`backend/fashx/profile/validation.py`)

`VALIDATION_POLICY_VERSION = "1.0"` separates validation into:
1. **Schema & Precision Validation**:
   - Rejects non-finite, zero, negative, or $>3$ decimal-place values.
   - Rejects unknown field codes.
2. **Hard Technical Bounds (`[1.00, 500.00]`)**:
   - Blocks technically corrupt inputs immediately with HTTP 422.
3. **Provisional Plausibility Bounds (`RANGES`)**:
   - Body fields have field-specific provisional bounds (e.g., Chest `35–180 CM`, Waist `30–180 CM`, Hip `35–200 CM`, Inseam `20–120 CM`, Height `100–230 CM`).
   - Values outside provisional bounds (within hard technical bounds) return `NEEDS_CONFIRMATION` with a respectful prompt asking the shopper to double-check, or proceed as `WARNING` when `confirm_unusual = true` is explicitly sent. Values are never silently clipped.
