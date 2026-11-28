# Profile & Onboarding Integration

- **Screens & State**: `mobile/app/onboarding/welcome.tsx` and `mobile/src/features/onboarding/screens/*` capture privacy acknowledgment, consent, basic profile, optional height/body measurements, and fit/style/color preferences in `useOnboardingStore`.
- **Persistence**: `onboardingService.saveProfileDraft()` (`mobile/src/features/onboarding/onboarding.service.ts`) persists profile attributes via `PATCH /profile/me`, body measurements via `fitProfileApi.addMeasurements()`, and default fit preference via `fitProfileApi.updateDefaultPreference()`.
- **Completion**: `completeOnboarding()` saves the draft and resets the transient Zustand store so stale draft data does not leak across sessions.
- **Known Gap**: `onboardingService.getProgress()` expects `GET /api/v1/onboarding/progress`, which is not yet mounted on the backend `onboarding_router`.
