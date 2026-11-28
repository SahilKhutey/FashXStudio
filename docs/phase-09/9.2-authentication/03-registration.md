# 03 — Registration

## Implementation
- `mobile/src/features/auth/RegisterScreen.tsx` & `mobile/app/(auth)/register.tsx`:
  - Collects full name, email (normalized lowercase), password (min 12 chars), password confirmation, and explicit Terms & Privacy acceptance.
  - Prevents duplicate concurrent submissions while loading.
  - Routes `VERIFICATION_REQUIRED` responses to `/(auth)/verify` without logging passwords.
  - Delegates account creation to `authProviderService.register(...)`.
