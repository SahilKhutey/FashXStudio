# 01 — Mobile Toolchain Audit

## Observed Toolchain Versions
| Item | Observed Version / Value |
| :--- | :--- |
| Node.js | `v24.18.0` |
| npm | `11.16.0` (lockfile: `mobile/package-lock.json`) |
| Expo CLI | `57.0.32` |
| Expo SDK (`package.json`) | `~57.0.31` |
| React | `19.2.3` |
| React Native | `0.86.3` |
| Expo Router | `~57.0.29` |
| TypeScript | `~6.0.3` |
| ESLint | `^10.12.0` |
| Jest / `jest-expo` | `~29.7.0` / `~57.0.6` |

## Findings & Notes
- Package manager is `npm` using `mobile/package-lock.json`.
- No dependency upgrades were required; all core Phase 09.1 packages (`expo-router`, `zustand`, `@tanstack/react-query`, `zod`, `expo-secure-store`, `expo-camera`, `expo-image`) are already installed and compatible with Expo SDK 57.
- In the Windows sandbox, `npx expo` telemetry attempts to create `C:\Users\ASUS\.expo`; setting `EXPO_NO_TELEMETRY=1` avoids this and allows `npx expo config --type public` to succeed cleanly.
- `npx expo-doctor` and `npx expo install --check` require network access to the Expo/npm registry and remain unverified offline in the sandbox.
