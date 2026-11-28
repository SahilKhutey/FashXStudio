# Phase 09 Repository Audit

## Verified Present in Repository

- **Mobile Foundation (9.1)**: `mobile/app.config.ts`, `mobile/eas.json`, `mobile/src/config/environment.ts`, `mobile/src/api/client.ts`, `mobile/src/stores/app.store.ts`, `mobile/src/components/EnvironmentIndicator.tsx`.
- **Auth (9.2)**: `mobile/src/auth/auth.service.ts`, `mobile/src/auth/auth.provider.ts`, `mobile/src/auth/logout.ts`, `mobile/src/auth/refresh-manager.ts`, `mobile/src/auth/adapters/supabase/supabase.provider.ts`, `mobile/src/features/auth/*`.
- **Onboarding & Profile (9.3)**: `mobile/src/features/onboarding/*`, `mobile/src/features/profile/profile.queries.ts`, `mobile/app/onboarding/welcome.tsx`.
- **Discovery (9.4)**: `mobile/app/(tabs)/explore.tsx`, `mobile/src/features/search/search.api.ts`, `mobile/src/features/catalog/flatten-pages.ts`.
- **PDP & Redirect (9.5)**: `mobile/src/features/product-detail/*`, `mobile/app/products/[productId].tsx`, `backend/fashx/catalog/detail/redirect_validator.py`.
- **Camera & VTO (9.6)**: `mobile/src/features/tryon/*`, `mobile/app/tryon/capture.tsx`.
- **Wardrobe & Looks (9.7)**: `mobile/src/features/wardrobe/*`, `mobile/app/wardrobe/looks/create.tsx`, `backend/fashx/commerce_wardrobe/looks/*`.
- **Quality & Accessibility (9.8)**: `mobile/src/hooks/*`, `mobile/src/components/*`, `mobile/src/services/crashReporting.ts`, `mobile/src/features/camera/permissionPolicy.ts`.

## Open Route-Wiring Gaps Found During 9.9 Audit

Inspection of `fashx.main.create_app().openapi()["paths"]` shows that while core Phase 09 endpoints (`/api/v1/me`, `/api/v1/profile/me`, `/api/v1/onboarding/style-quiz`, `/api/v1/search/products`, `/api/v1/feed`, `/api/v1/tryon/jobs`, `/api/v1/wardrobe/items`) are mounted, three Phase 09 mobile endpoint paths are not yet mounted in `backend/fashx/main.py`:

1. `backend/fashx/catalog/detail/router.py` (`/catalog/products/{product_id}/detail`, `/catalog/offers/{offer_id}/redirect`) is not yet included in `create_app()`.
2. `backend/fashx/commerce_wardrobe/looks/router.py` (`/wardrobe/looks`) is not yet included in `create_app()`.
3. `onboardingService.getProgress()` calls `GET /onboarding/progress`, which is not yet exposed on `onboarding_router`.

These are tracked in `BUG_REGISTER.md` as open pre-staging blockers.
