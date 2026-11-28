# 07 — Height and Measurements

- `mobile/src/features/onboarding/components/HeightInput.tsx`: optional height input supporting `CM` and `IN` (`inches * 2.54`), validated within `50–250 cm`, with `Skip for now`.
- `mobile/src/features/onboarding/screens/MeasurementsScreen.tsx`: optional body measurements (`CHEST`, `WAIST`, `HIP`, `SHOULDER`, `INSEAM`, `SLEEVE_LENGTH`) submitted via `fitProfileApi.addMeasurements` with `unit: "CM"` and `measurement_method: "SELF_MEASURED"`.
