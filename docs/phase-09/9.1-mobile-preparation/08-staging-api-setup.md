# 08 — Staging API Setup

## Configuration
- `mobile/eas.json` `staging` profile sets:
  - `APP_ENV=staging`
  - `EXPO_PUBLIC_APP_ENV=staging`
  - `EXPO_PUBLIC_API_URL=https://staging-api.fashxstudio.com`
  - `EXPO_PUBLIC_API_BASE_URL=https://staging-api.fashxstudio.com`
  - `EXPO_PUBLIC_DEV_TOKEN_LOGIN=0`
  - `EXPO_PUBLIC_ENABLE_DEV_TOOLS=false`
- `parseEnvironment` enforces HTTPS for `staging`.

## Verification Status
- Staging backend smoke tests (login, catalog, search, fit, VTO, logout) remain `PENDING` until staging API deployment and device build execution.
