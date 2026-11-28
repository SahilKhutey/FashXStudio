# 16 — Data Validation

- `HeightInput`: validates numeric input, converts inches (`* 2.54`), enforces `50–250 cm` envelope.
- `MeasurementsScreen`: validates positive numeric values (`0 < v <= 300`).
- `mobile/src/features/onboarding/schemas.ts`: preserves `step1Schema`, `step2Schema`, `step3Schema`, and `onboardingProfileSchema`.
