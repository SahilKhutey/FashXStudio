# 12 — Mobile Fit Profile UI

Implemented in `mobile/src/features/fit-profile/`:
- `types.ts`: TypeScript contracts aligned with OpenAPI `schema.d.ts`.
- `api/fitProfileApi.ts`: Uses authenticated `api()` client from `mobile/src/api/client.ts`.
- `store/fitProfileStore.ts`: Ephemeral in-memory Zustand state with `clearProfile()` for logout/deletion/consent withdrawal (never persists measurements to unsecured storage).
- `components/MeasurementGuidanceCard.tsx`: Plain-language tape instructions & examples.
- `components/MeasurementInput.tsx`: Numeric `decimal-pad` input, unit switcher (`CM`/`IN`/`MM` or `KG`), client normalized preview, inline error alerts, and confirm-before-replace prompt.
- `components/FitPreferenceSelector.tsx`: Subjective fit preference selector with disclaimer.
- `screens/FitProfileScreen.tsx`: Privacy notice, consent grant/withdrawal toggle, per-measurement timestamps, edit/delete actions, and full deletion control.
