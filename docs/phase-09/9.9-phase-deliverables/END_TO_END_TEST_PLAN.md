# End-to-End Test Plan

## Automated Verification (Executed Locally)

1. **Mobile Cross-Phase Exit Gate** (`mobile/__tests__/phase09_9_exit_gate.test.tsx`):
   - HTTPS enforcement in staging/production (`parseEnvironment`)
   - Auth registration, verification, session refresh, and account-isolated logout (`ProviderAuthService`, `performAppLogout`, `wardrobeKeys`)
   - Onboarding draft save & completion reset (`useOnboardingStore`, `onboardingService`, `completeOnboarding`)
   - Search & multi-merchant offer deduplication (`searchProducts`, `flattenSearchPages`)
   - PDP detail & availability checks (`fetchProductDetail`, `availabilityMessage`, `canPurchase`)
   - VTO submission, polling, cancellation, and error mapping (`submitTryOnJob`, `getTryOnJob`, `cancelTryOnJob`, `mapTryOnErrorCode`)
   - Saved look creation/deletion & merchant redirect (`createSavedLook`, `deleteSavedLook`, `requestMerchantRedirect`)
   - Crash report redaction (`captureSafeError`)
2. **Backend Exit Gate** (`tests/unit/phase_09/test_phase09_exit_gate.py`):
   - FastAPI route mounting in `create_app()`
   - Outbound merchant URL validation (`validate_merchant_url`)
   - Saved look ownership/creation service (`create_saved_look_for_user`)

## Staging & Hardware Verification (Pending)

- Full golden journey against live staging API, Postgres database, Supabase Auth, S3/media storage, and VTO inference provider on physical Android and iOS builds.
