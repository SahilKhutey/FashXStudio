# 15 — Profile Editing

- Existing edit screens (`EditPhysicalProfileScreen`, `EditShoppingPreferencesScreen`, `EditStylePreferencesScreen`, `FitProfileScreen`) remain preserved.
- `mobile/src/features/profile/profile.queries.ts` (`useMyProfile`, `useSaveMyProfile`) updates TanStack Query `profileKeys.me()` cache and invalidates `["fit"]` and `["ranking"]` queries after profile mutations.
