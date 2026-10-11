# ADR-0007: Mobile Authentication Provider

## Status
Accepted

## Date
2026-10-11

## Context
For the FashX Mobile MVP (Phase 8), invited pilot testers in India need a reliable, friction-free authentication flow to sign in, provide consent, set up a profile, and access virtual try-on.

In India, SMS-based phone OTP authentication is heavily constrained by TRAI Distributed Ledger Technology (DLT) regulations, which mandate business entity registration, sender ID (header) approvals, pre-registered SMS content templates, and commercial telemarketer contracts. On top of DLT, SMS providers (Twilio, MessageBird, TextLocal) incur per-message fees and delivery delays. Requiring phone OTP for an invite-only closed pilot introduces unnecessary legal and operational overhead.

Furthermore, integrating third-party social logins (such as Google or Apple) triggers App Store Review Guidelines Section 4.8, requiring Sign in with Apple alongside any other third-party social login, along with native module dependencies.

The backend authentication architecture (established in Phase 3) was intentionally designed to decouple identity verification from internal authorization. The backend uses a provider-neutral `TokenVerifier` port (with `JWKSVerifier` for production and `LocalJWTVerifier` for hermetic testing). Claims `(issuer, sub)` are mapped deterministically to internal `user_id` records in `auth_identities`.

## Options Considered

| Option | Pros | Cons |
| :--- | :--- | :--- |
| **Supabase Auth, email OTP** *(Recommended & Selected)* | Pure-JavaScript client (no native modules), RS256/ES256 JWKS verification natively supported by Phase 3 backend `JWKSVerifier`, invite-only pilot enforced via disabling public sign-ups, no TRAI DLT registration overhead. | Hosted service dependency; default transactional email quota requires custom SMTP for high volume. |
| **Firebase Auth** | Google-backed infrastructure, strong social sign-in. | Requires native modules and config plugins (`@react-native-firebase`), phone auth faces identical TRAI DLT regulations. |
| **Custom In-House Auth** | Complete stack ownership. | Highest engineering effort, security risk, and ongoing maintenance burden for email verification, rate limiting, and token rotation; rejected. |

## Decision
Adopt **Supabase Auth with Email OTP (6-digit code)** for the mobile client:
1. **Invite-Only Pilot:** Public sign-ups are disabled in the Supabase project. Pilot testers are invited by email, ensuring controlled access.
2. **Email Verification Code:** The magic link template is configured to output `{{ .Token }}` with a 10-minute expiry, allowing users to enter a 6-digit code on mobile without leaving the app to click external deep links.
3. **Asymmetric Key Rotation (JWKS):** The Supabase project is configured with asymmetric RS256 signing keys, serving public keys at `https://<ref>.supabase.co/auth/v1/.well-known/jwks.json`.
4. **Backend Verification:** The backend `JWKSVerifier` verifies incoming Bearer tokens against the Supabase JWKS endpoint with audience `authenticated` and issuer `https://<ref>.supabase.co/auth/v1`. Roles and permissions remain strictly in the backend database.
5. **Secure Storage on Client:** Supabase sessions on mobile are persisted using the "large secure store" pattern: an encryption key stored in `expo-secure-store`, and the encrypted session payload stored in `@react-native-async-storage/async-storage`.

## Consequences
- **Positive:** Zero TRAI DLT paperwork or carrier registration for the pilot. Pure JS mobile integration without native linkers. Standard RFC-7519 / RFC-7517 JWT/JWKS verification.
- **Subsequent Phases:** Post-pilot growth can introduce Google Sign-In and phone OTP once DLT registration is justified.
- **Rollback:** The backend verifier is completely provider-neutral. Switching providers requires changing four environment variables (`AUTH_MODE`, `AUTH_ISSUER`, `AUTH_AUDIENCE`, `AUTH_JWKS_URL`) and the mobile sign-in UI, with zero changes to domain models, database schema, or authorization policies.
