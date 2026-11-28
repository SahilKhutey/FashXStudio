# 13 — Mobile Permissions

## Least-Privilege Matrix
- **Camera**: Requested only when entering VTO camera capture (`CameraCapture.tsx` / `usePhotoUpload.ts`).
- **Photo Library**: Requested only when shopper selects an existing photo; `expo-image-picker` plugin sets `photosPermission: false` to avoid broad startup manifest claims.
- **Microphone (`RECORD_AUDIO`)**: Explicitly blocked via `android.blockedPermissions: ["android.permission.RECORD_AUDIO"]` and `recordAudioAndroid: false` on `expo-camera`.
- **Location**: Not requested.

## Permission State Model (`mobile/src/services/camera.service.ts`)
- `PermissionState`: `"UNKNOWN" | "GRANTED" | "DENIED" | "BLOCKED" | "UNAVAILABLE"`.
- `toPermissionState` tested in `mobile/__tests__/phase09_1_foundation.test.ts`.
