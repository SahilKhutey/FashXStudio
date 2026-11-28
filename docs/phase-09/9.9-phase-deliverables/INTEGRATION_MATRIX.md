# Phase 09 Integration Matrix

Status legend: `MOCK` | `LOCAL` | `SANDBOX_VERIFIED` | `PRODUCTION_VERIFIED`

| Capability | Mobile Implementation | Backend / Provider | Current Status | Notes |
|---|---|---|---|---|
| Environment & HTTPS enforcement | `parseEnvironment` | N/A | `LOCAL` | Rejects HTTP in staging/production |
| Registration / Login / Verify / Recovery | `ProviderAuthService`, `supabase.provider.ts` | Supabase Auth | `LOCAL` | Live Supabase sandbox `PENDING` |
| Token storage & single-flight refresh | `secureStorage.ts`, `refresh-manager.ts`, `api/client.ts` | Auth provider | `LOCAL` | Verified in Jest |
| Onboarding draft & profile save | `useOnboardingStore`, `onboardingService.saveProfileDraft` | `/api/v1/profile/me`, `/api/v1/profile/fit/*` | `LOCAL` | `/onboarding/progress` gap open |
| Feed & Explore search | `searchProducts`, `flattenSearchPages` | `/api/v1/feed`, `/api/v1/search/products` | `LOCAL` | Live catalog DB query `PENDING` |
| PDP & Merchant redirect | `fetchProductDetail`, `requestMerchantRedirect` | `catalog/detail/redirect_validator.py` | `LOCAL` | Router wiring into `main.py` open |
| Camera & photo upload | `permissions.ts`, `imageValidation.ts`, `PhotoPreview.tsx` | `/api/v1/media/*` | `LOCAL` | Physical device camera `NOT_TESTED` |
| Virtual Try-On (VTO) | `submitTryOnJob`, `getTryOnJob`, `cancelTryOnJob` | `/api/v1/tryon/jobs` | `LOCAL` | Live VTO provider `PENDING` |
| Closet & Saved Looks | `useUserWardrobe`, `useSavedLooks`, `createSavedLook` | `/api/v1/wardrobe/items`, `looks/service.py` | `LOCAL` | `/wardrobe/looks` router wiring open |
| Crash reporting PII/token redaction | `captureSafeError`, `redactSensitiveText` | Sentry/sink | `LOCAL` | Signed URL redaction fixed in 9.9 |
| Physical Android & iOS golden journey | Full app | Staging API + Postgres | `MOCK` / `PENDING` | Hardware testing `NOT_TESTED` locally |
