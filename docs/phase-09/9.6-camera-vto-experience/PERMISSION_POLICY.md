# Permission Policy

- `requestGalleryAccess()` (`mobile/src/features/tryon/permissions.ts`) and `toPermissionState()` (`mobile/src/services/camera.service.ts`) handle `GRANTED`, `DENIED`, and `BLOCKED` states cleanly without crashing or auto-uploading.
