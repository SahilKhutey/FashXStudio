# 06 — Environment Configuration

## Implementation
- `mobile/src/config/environment.ts` exports `parseEnvironment(raw)` and `environment` validated with `zod`:
  - `APP_ENV` and `EXPO_PUBLIC_APP_ENV` must be `development` | `staging` | `production` and must match if both are provided.
  - `staging` and `production` reject `http://` API URLs (HTTPS mandatory).
  - `enableDevTools` is forced `false` in `production`.
- `mobile/src/lib/env.ts` preserves `validateRuntimeConfig` fail-closed guards for HTTPS and `allowDevAuth === false` in production.
- `mobile/src/components/EnvironmentIndicator.tsx` renders the environment label in non-production builds and returns `null` in production.
- `mobile/.env.example` documents non-secret template variables.

## Verification
- Verified by `mobile/__tests__/runtime_config.test.ts` and `mobile/__tests__/phase09_1_foundation.test.ts`.
