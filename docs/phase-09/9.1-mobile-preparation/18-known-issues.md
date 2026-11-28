# 18 — Known Issues & Environment Gaps

1. **Expo CLI Telemetry in Windows Sandbox**: `npx expo` writes telemetry to `C:\Users\ASUS\.expo` unless `EXPO_NO_TELEMETRY=1` is set.
2. **Offline Registry Checks**: `npx expo-doctor` and `npx expo install --check` require npm/Expo registry network access and could not complete offline inside the sandbox.
3. **`app.json` Legacy File**: `mobile/app.json` remains in the repo alongside `mobile/app.config.ts` (Expo prioritizes `app.config.ts`); kept untouched to avoid breaking external references.
4. **Device & Staging Verification**: EAS builds (`android`/`ios`), physical camera/SecureStore validation, and live staging API smoke checks remain `PENDING`.
