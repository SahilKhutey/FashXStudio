# 02 — Dependency Audit

## Installed Core Groups (`mobile/package.json`)
- **Runtime**: `expo` (`~57.0.31`), `react` (`19.2.3`), `react-native` (`0.86.3`)
- **Navigation**: `expo-router` (`~57.0.29`), `react-native-screens` (`~4.26.2`), `react-native-safe-area-context` (`~5.7.0`), `expo-linking` (`~57.0.13`)
- **Client State**: `zustand` (`^5.0.8`)
- **Server State**: `@tanstack/react-query` (`^5.89.0`)
- **Validation**: `zod` (`^4.6.5`)
- **Auth & Storage**: `@supabase/supabase-js` (`^2.117.3`), `expo-secure-store` (`~57.0.4`), `@react-native-async-storage/async-storage` (`2.2.0`, used for non-sensitive config cache only)
- **Camera & Media**: `expo-camera` (`~57.0.6`), `expo-image-picker` (`~57.0.20`), `expo-image` (`~57.0.5`), `expo-image-manipulator` (`~57.0.21`), `expo-file-system` (`~57.0.7`)
- **Testing**: `jest` (`~29.7.0`), `jest-expo` (`~57.0.6`), `@testing-library/react-native` (`^14.1.0`)

## Rules Enforced
- Zero new dependencies added (`AGENTS.md` Rule 7).
- `npm ls --depth=0` exited `0` with all peer/installed dependencies resolved.
- Screens route network calls through `mobile/src/api/client.ts` and feature API modules rather than raw `fetch`.
