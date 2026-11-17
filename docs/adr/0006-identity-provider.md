# ADR-0006: Identity Provider — Amazon Cognito User Pools

> **Note on ADR Numbering:** In the original repository sequence, ADR-0006 was allocated to [Discovery Ranking Architecture](file:///c:/Users/ASUS/Documents/FashXStudio/docs/adr/0006-discovery-ranking.md). This document serves as the canonical record for Phase 04 Authentication and supersedes [ADR-0007 Mobile Authentication Provider](file:///c:/Users/ASUS/Documents/FashXStudio/docs/adr/0007-mobile-auth-provider.md). The full architecture record is also maintained at [ADR-0010 Identity Provider](file:///c:/Users/ASUS/Documents/FashXStudio/docs/adr/0010-identity-provider-cognito.md).

- **Status:** Accepted
- **Date:** 2026-11-15
- **Owner:** Sahil Khutey

---

## 1. Context and Decision Summary

FashXStudio adopts **Amazon Cognito User Pools** in `ap-south-1` (Mumbai) for shopper authentication across development, staging, and production environments.

### Key Architecture Principles:
1. **Cognito authenticates the shopper**; FashXStudio PostgreSQL stores the shopper's application profile, measurements, consent records, and wardrobe data.
2. **Cognito `sub` claim is the immutable external identity reference** mapped deterministically to internal `users.id` UUIDs via `auth_identities`.
3. **FastAPI independently validates access tokens** via RS256 JWKS public key rotation (`token_use="access"`, `client_id=expected_app_client_id`, `iss=expected_issuer`).
4. **Mobile app uses OAuth 2.0 Authorization Code Flow + PKCE** as a public client with no client secret.
5. **Database-backed session revocation** (`revoked_auth_sessions`) protects against accepted tokens post-logout.

For detailed alternative comparisons and security guarantees, refer to [ADR-0010](file:///c:/Users/ASUS/Documents/FashXStudio/docs/adr/0010-identity-provider-cognito.md).
