# 01 — Authentication Architecture

## Provider-Independent Boundary
- **Decision**: Retained `@supabase/supabase-js` (already installed and integrated with `LargeSecureStore` + FastAPI JWT verification) as the active `AuthProvider` adapter (`mobile/src/auth/adapters/supabase/supabase.provider.ts`), behind the provider-independent `AuthProvider` interface (`mobile/src/auth/auth.provider.ts`) and `ProviderAuthService` (`mobile/src/auth/auth.service.ts`).
- Removed the simulated `dummyAccess` token stub in `mobile/src/auth/authService.ts` and wired `signIn` to `authProviderService`.
- Zero new dependencies added (`AGENTS.md` Rule 7).
