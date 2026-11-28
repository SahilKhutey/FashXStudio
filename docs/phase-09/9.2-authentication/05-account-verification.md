# 05 — Account Verification

## Implementation
- `mobile/src/features/auth/VerificationScreen.tsx` & `mobile/app/(auth)/verify.tsx`:
  - Displays masked email (`maskEmail` in `mobile/src/auth/auth.types.ts`) instead of exposing full destination unnecessarily.
  - Validates 6-digit numeric verification code format before calling `authProviderService.confirmRegistration(...)`.
  - Supports bounded resend via `authProviderService.resendVerificationCode(...)`.
