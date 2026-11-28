# 17 — Privacy and Security

- Optional processing switches start `false` (unchecked).
- Model training is never bundled with personalization, VTO, or analytics consent.
- Skipped fields are never fabricated into measurements or size conversions.
- Draft store (`useOnboardingStore`) is in-memory only and never persisted to unencrypted storage.
