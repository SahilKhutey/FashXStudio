# 14 — Onboarding Progress and Resume

- `OnboardingStatus` (`NOT_STARTED`, `IN_PROGRESS`, `BASIC_PROFILE_COMPLETE`, `OPTIONAL_DETAILS_PENDING`, `COMPLETED`, `SKIPPED`, `NEEDS_RECONSENT`).
- `useOnboardingStore` tracks `currentStep` and `draft.skippedSteps` in memory; `completeOnboarding()` resets the draft only after backend confirmation.
- `getRouteDecision()` (`mobile/src/navigation/route-policy.ts`) resumes incomplete required onboarding steps safely.
