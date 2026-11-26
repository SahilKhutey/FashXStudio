# 03 — Shopper Measurement Guidance

## 1. Plain-Language Guidance Registry

Defined in `backend/fashx/profile/measurement_definitions.py` and exposed via `GET /api/v1/profile/fit/definitions`.

Every supported field includes:
- Shopper-facing `display_name`
- Plain-language `explanation`
- Exact `tape_positioning` instructions
- Guidance on `how_to_hold` (relaxed, comfortable clearance, never pulling tight)
- Example input format (`example_input`)
- Supported garment categories and default unit

## 2. Registered Body Measurement Fields

| Code | Name | Measurement Type | Optional Contextual Only |
|---|---|---|---|
| `CHEST` | Chest | Circumference | No |
| `BUST` | Bust | Circumference | No |
| `WAIST` | Waist | Circumference | No |
| `HIP` | Hips | Circumference | No |
| `SHOULDER` | Shoulder width | Linear | No |
| `SLEEVE_LENGTH` | Sleeve length | Linear | No |
| `INSEAM` | Inseam | Linear | No |
| `OUTSEAM` | Outseam | Linear | No |
| `THIGH` | Thigh | Circumference | No |
| `NECK` | Neck | Circumference | No |
| `HEIGHT` | Height | Linear | Yes |
| `WEIGHT` | Weight | Weight | Yes (not a substitute for body measurements) |
