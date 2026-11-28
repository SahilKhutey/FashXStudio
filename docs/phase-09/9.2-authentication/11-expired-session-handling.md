# 11 — Expired-Session Handling

## Behavior
- `getRouteDecision()` (`mobile/src/navigation/route-policy.ts`) redirects unauthenticated/expired sessions to `/(auth)/sign-in` before protected `(tabs)` routes render.
- `SupabaseAuthProvider.refreshSession()` maps missing/invalid refresh sessions to `AuthError("SESSION_EXPIRED", ..., false)`.
- `403` authorization errors are normalized to `ApiError` and do not trigger logout or token refresh loops.
