# 14 — Security Requirements

- No passwords, verification codes, recovery codes, or tokens logged.
- Simulated `dummyAccess` stub removed from `mobile/src/auth/authService.ts`.
- Tokens persisted only in `expo-secure-store` (`WHEN_UNLOCKED_THIS_DEVICE_ONLY`), never in `AsyncStorage` or Zustand persistence.
- `maskEmail` masks destination emails on verification UI.
- Dev-token login disabled in production (`validateRuntimeConfig` and `parseEnvironment`).
