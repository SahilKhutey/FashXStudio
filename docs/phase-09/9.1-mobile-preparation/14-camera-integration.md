# 14 — Camera Integration

## Implementation
- `mobile/src/services/camera.service.ts`: Centralized import boundary for `expo-camera` (`Camera`, `CameraView`, `useCameraPermissions`, `toPermissionState`).
- `mobile/src/features/tryon/CameraCapture.tsx`: Requests camera permission on entry, handles `UNKNOWN`, `DENIED`, and `BLOCKED` (with `Linking.openSettings()`) states, captures still photo with `takePictureAsync`, and passes local URI to caller without auto-uploading.
- `mobile/src/features/media/`: Existing photo picker, local pre-validation, and consent-gated upload pipeline preserved.

## Verification Status
- Unit tests for `toPermissionState` pass; physical Android/iOS camera capture verification remains `PENDING`.
