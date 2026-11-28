# Account Isolation and Privacy

- **Token & Cache Cleanup**: `performAppLogout()` (`mobile/src/auth/logout.ts`) clears SecureStore credentials and session state; `wardrobeKeys` partitions query caches by `userId` (`["account", userId, "wardrobe", ...]`).
- **Crash Reporting Redaction**: `captureSafeError()` and `redactSensitiveText()` (`mobile/src/services/crashReporting.ts`) scrub Bearer tokens, signed query URLs (`?X-Amz-Signature=...` / `signature=...`), `data:image/...;base64,...` strings, and `file://` paths before dispatching error telemetry.
- **9.9 Fix Applied**: Updated `SENSITIVE_PATTERN` in `mobile/src/services/crashReporting.ts` so the entire signed query string (including the signature value after `=`) is redacted instead of stopping at the parameter name.
