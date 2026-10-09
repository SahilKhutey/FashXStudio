# Threat model (MVP)

**Assets:** reference photos and body data (biometric), profile and preferences, closet, try-on results, session analytics.  
**Actors:** anonymous internet, a logged-in user attacking other users, a stolen/expired token, a malicious upload, an insider with DB access.

| # | Threat | Mitigation (Phase 3 unless noted) |
|---|---|---|
| T1 | Unauthenticated access to any API route | Default-deny routers + route-coverage test |
| T2 | User A reads/deletes user B's photos or profile (IDOR) | `require_self` on `{user_id}`; owner-scoped repository queries; 403/404 |
| T3 | Forged, expired, wrong-audience or `alg=none` tokens | Pinned algorithms, required exp/sub/iss/aud, verifier tests |
| T4 | Privilege escalation to catalog/analytics admin routes | DB-held roles; `require_role("admin")`; admin has no biometric access |
| T5 | Malicious/oversized/decompression-bomb image upload | Size cap, format allowlist, pixel cap, re-encode (strips EXIF/GPS) |
| T6 | Cost abuse of GPU try-on and uploads | Per-user Redis rate limits; stricter on try-on and upload |
| T7 | Secrets or tokens in logs/repo | Fail-fast settings, no default secrets, log redaction, gitleaks in CI |
| T8 | Browser/transport weaknesses | Security headers, strict CORS, docs off in prod, HTTPS at the proxy (Phase 9) |
| T9 | Photos readable via storage URLs | Private bucket + signed URLs with strict TTL (Phase 4: S3Storage/LocalStorage + MediaObject key tracking) |
| T10 | Consent revoked but data remains | Cascading erasure pipeline, Outbox StoragePurgeRequested, table classification guard (Phase 4: test_erasure.py) |
