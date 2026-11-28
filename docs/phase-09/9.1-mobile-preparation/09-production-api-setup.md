# 09 — Production API Setup

## Configuration
- `mobile/eas.json` `production` profile sets:
  - `APP_ENV=production`
  - `EXPO_PUBLIC_APP_ENV=production`
  - `EXPO_PUBLIC_API_URL=https://api.fashxstudio.com`
  - `EXPO_PUBLIC_API_BASE_URL=https://api.fashxstudio.com`
  - `EXPO_PUBLIC_DEV_TOKEN_LOGIN=0`
  - `EXPO_PUBLIC_ENABLE_DEV_TOOLS=false`
- `EnvironmentIndicator` returns `null` in `production`.
- `parseEnvironment` and `validateRuntimeConfig` fail closed on HTTP URLs or enabled dev authentication in production.
