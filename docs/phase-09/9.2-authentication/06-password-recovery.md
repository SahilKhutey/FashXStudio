# 06 — Password Recovery

## Implementation
- `mobile/src/features/auth/RecoveryScreen.tsx` & `mobile/app/(auth)/forgot-password.tsx`:
  - Step 1: Requests recovery code via `authProviderService.startRecovery(...)` with generic non-enumerating confirmation copy.
  - Step 2: Validates 6-digit recovery code and 12+ character matching new password before calling `authProviderService.completeRecovery(...)`.
