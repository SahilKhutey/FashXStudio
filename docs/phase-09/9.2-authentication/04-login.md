# 04 — Login

## Implementation
- `mobile/src/features/auth/LoginScreen.tsx`:
  - Normalizes email, masks password input, clears password on failed authentication, and maps provider failures via `toAuthUserMessage`.
  - Routes `VERIFICATION_REQUIRED` accounts directly to verification and links to `/(auth)/register` and `/(auth)/forgot-password`.
- `mobile/app/(auth)/sign-in.tsx`: Preserves existing OTP pilot sign-in while linking to `/(auth)/register` and `/(auth)/forgot-password`.
