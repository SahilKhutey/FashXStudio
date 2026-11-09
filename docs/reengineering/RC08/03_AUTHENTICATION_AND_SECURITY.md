# RC08 — Authentication & Security Hardening

## 1. Identity & Token Verification
Staging and production enforce JWKS-based JWT signature and claims verification against Supabase Auth:
- **Algorithm**: RS256 / ES256 via PyJWKClient with key caching.
- **Audience & Issuer**: Exact matching against configured `AUTH_AUDIENCE` and `AUTH_ISSUER`.
- **Clock Skew**: 60-second tolerance on `exp` / `nbf`.
- **Development Login Gate**: Route `/api/v1/auth/demo-token` and mock token generation are strictly locked behind `env != "prod"` and `auth_mode == "local"`.

## 2. Resource Isolation & Zero-Trust Access Control
Every private resource enforces tenant and user isolation:
- **Wardrobe**: `user_id` in token must match `item.user_id`. Accessing another user's wardrobe item returns 404 (preventing user enumeration).
- **Virtual Try-On Jobs**: Only the owning `user_id` can query job status or retrieve rendered try-on image artifacts.
- **Photos & Measurement Profiles**: Direct DB queries are scoped strictly to `current_user.id`.

## 3. Threat Mitigation Matrix
| Threat | Mitigation Mechanism | Implementation |
|---|---|---|
| Insecure Direct Object Reference (IDOR) | Scoped repository queries on `user_id` | `ProfileUnitOfWork`, `CommerceWardrobeUnitOfWork` |
| Server-Side Request Forgery (SSRF) | IP range filtering on retailer image/URLs | `fashx/catalog/images/validator.py` |
| Malicious File Uploads | MIME-type sniffing, byte magic checks, dimension bounding | `ImageValidator` (max 8MB, min 128x128, max 20MP) |
| Credential Exposure | Backend-only secrets, runtime injection, no credentials logged | Gitleaks scan in CI, `SecretStr` in Pydantic |
| Denial of Service / Abuse | Redis-backed rate limiting on sensitive routes | Slowapi rate limiter on auth, upload, and try-on routes |
| Open Redirects | Whitelist domain validation on retailer redirects | `retailer_allowed_hosts` set in settings |
