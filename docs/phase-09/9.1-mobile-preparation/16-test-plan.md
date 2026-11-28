# 16 — Phase 09.1 Test Plan

## Automated Suites (Executed Locally)
- `mobile/__tests__/phase09_1_foundation.test.ts`: Environment validation (`MOB-ENV`), `useAppStore` (`MOB-STATE`), `ProductSummarySchema` (`MOB-API`), `toPermissionState` (`MOB-PERM`), `secureStorage` (`AUTH-MOB`).
- `mobile/__tests__/runtime_config.test.ts`: Production HTTPS and dev-token fail-closed guards.
- `mobile/src/api/client.test.ts`: Bearer auth, 204 handling, error normalization, timeouts, single-flight 401 refresh.
- `mobile/src/navigation/__tests__/route-policy.test.ts`: Auth & onboarding route-guard decisions.
- `mobile/__tests__/auth_and_api.test.ts`, `dev_token_gate.test.ts`, `capture_privacy.test.ts`, `photo_upload.test.ts`, `file_cleanup.test.ts`, `settings_and_privacy.test.ts`, and feature suites (`29` suites total).

## Pending Device & Staging Tests
- EAS Android/iOS build generation and installation (`MOB-AND`, `MOB-IOS`).
- Physical-device camera capture and SecureStore restart persistence (`MOB-CAM`, `AUTH-MOB-004`).
- Staging API end-to-end smoke test suite.
