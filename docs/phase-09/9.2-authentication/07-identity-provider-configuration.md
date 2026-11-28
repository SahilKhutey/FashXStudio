# 07 — Identity Provider Configuration

## Active Configuration
- Active adapter: `SupabaseAuthProvider` (`mobile/src/auth/adapters/supabase/supabase.provider.ts`) using `mobile/src/lib/supabase.ts` (`LargeSecureStore` backed by `expo-secure-store`).
- Cognito configuration scaffolding (`mobile/src/auth/amplify.ts`) remains isolated behind `AuthProvider` if AWS Cognito migration is scheduled later.
- Live identity-provider environment provisioning and backend JWKS validation against staging remain `PENDING`.
