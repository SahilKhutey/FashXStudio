# Crash Reporting Policy

- `mobile/src/services/crashReporting.ts` (`initializeCrashReporting`, `captureSafeError`, `redactSensitiveText`) strips Bearer tokens, signed S3 URLs, base64 image payloads, and local `file://` photo URIs before forwarding to the configured crash sink.
