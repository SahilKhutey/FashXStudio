# 12 — iOS Build Configuration

## Configuration (`mobile/app.config.ts` & `mobile/eas.json`)
- `ios.supportsTablet: true` with environment-scoped `bundleIdentifier` (`com.fashxstudio.app.dev`, `com.fashxstudio.app.staging`, `com.fashxstudio.app`).
- `ios.infoPlist.NSCameraUsageDescription`: `"FashX uses the camera so you can take the photo used for virtual try-on. Photos are only used with your consent."`

## Verification Status
- `eas build --platform ios --profile development` / `staging` cloud builds and physical iPhone installation remain `PENDING` (requires EAS cloud / macOS Xcode + Apple signing credentials).
