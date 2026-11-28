# 01 — Onboarding Architecture

- Reuses existing `mobile/src/features/profile/` (`profileApi`, edit screens), `mobile/src/features/fit-profile/` (`fitProfileApi`, `FitProfileScreen`), and `mobile/app/onboarding/` (`consent.tsx`, `profile.tsx`, `quiz.tsx`, `capture.tsx`).
- Adds structured onboarding screens, components, draft store, and service in `mobile/src/features/onboarding/`, plus TanStack Query server-state hooks in `mobile/src/features/profile/profile.queries.ts`.
- Separates consent submission (`savePurposeConsent`) from profile persistence (`onboardingService.saveProfileDraft`).
