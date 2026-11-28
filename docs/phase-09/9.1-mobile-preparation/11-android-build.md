# 11 — Android Build Configuration

## Configuration (`mobile/app.config.ts` & `mobile/eas.json`)
- Managed Expo workflow with `eas.json` profiles: `development`, `staging`, `preview`, `production`.
- `android.allowBackup: false`, `softwareKeyboardLayoutMode: "resize"`.
- `android.permissions: ["android.permission.CAMERA"]` and `android.blockedPermissions: ["android.permission.RECORD_AUDIO"]`.

## Verification Status
- Expo public config validated via `npx expo config --type public`.
- `eas build --platform android --profile development` / `staging` cloud builds and physical APK installation remain `PENDING`.
