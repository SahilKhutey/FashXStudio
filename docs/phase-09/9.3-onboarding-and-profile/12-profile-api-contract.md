# 12 — Profile API Contract

- `GET/PATCH /api/v1/profile/me` (`profileApi.getProfile`, `profileApi.updateProfile`)
- `POST /api/v1/profile/fit/measurements` (`fitProfileApi.addMeasurements`)
- `PUT /api/v1/profile/fit/preferences` (`fitProfileApi.updateDefaultPreference`)
- `PUT /api/v1/profile/fit/consents/{purpose}` (`savePurposeConsent` / `fitProfileApi.updateConsent`)
- `GET /api/v1/onboarding/progress` (`onboardingService.getProgress`)
