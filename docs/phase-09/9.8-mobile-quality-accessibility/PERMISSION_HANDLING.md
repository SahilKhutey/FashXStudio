# Permission Handling

- `getCameraPermissionAction()` (`mobile/src/features/camera/permissionPolicy.ts`) maps `unknown`, `granted`, `denied`, and `blocked` to deterministic UI actions (`REQUEST_PERMISSION`, `CONTINUE_CAPTURE`, `SHOW_DENIAL_HELP`, `OPEN_SETTINGS`).
