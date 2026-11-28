# 07 — Development API Setup

## Configuration
- `.env.example` defaults to `http://localhost:8000` for workstation/iOS simulator development.
- `mobile/eas.json` `development` profile configures `APP_ENV=development`, `EXPO_PUBLIC_APP_ENV=development`, and `http://10.0.2.2:8000` for Android emulators.
- Physical devices on a local LAN should set `EXPO_PUBLIC_API_URL` / `EXPO_PUBLIC_API_BASE_URL` to the workstation LAN IP (`http://<LAN_IP>:8000`) in local `.env` (gitignored).

## Verification Status
- Local workstation backend connectivity and physical-device LAN verification are `PENDING` (no physical device attached in this environment).
