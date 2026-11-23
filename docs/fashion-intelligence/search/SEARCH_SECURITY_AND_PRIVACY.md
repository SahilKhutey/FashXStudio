# Search Security, Privacy & Tenant Isolation

## 1. Compliance with Rule I06 (Biometric & Personal Media Privacy)
- Shopper reference images used in visual search are isolated to temporary memory/staging; they are **never committed to long-term storage** and **never merged into catalog embedding tables**.
- No facial recognition, body scanning, or biometric feature extraction is performed during search.
- Queries are executed on self-hosted infrastructure. No shopper search queries or uploaded images are dispatched to unapproved third-party SaaS search engines.

---

## 2. Multi-Tenant Authorization & Access Controls
- **Shopper Search vs Admin Search**: Shopper-facing endpoints return public, active, in-stock catalog listings only. Administrative and merchant-specific endpoints are segregated under `/api/v1/admin/catalog/*` with RBAC checks.
- **Tenant Isolation**: B2B merchant queries are strictly scoped to the requesting merchant's authorized catalog sources.
- **Query Injection Prevention**: Full-text queries are passed through parameterized statements and sanitization routines; direct SQL string formatting is strictly prohibited.
- **Rate Limiting & Abuse Prevention**: High-compute endpoints (`POST /api/v1/search/visual`, `POST /api/v1/search/semantic`) have per-client rate limits to prevent GPU resource starvation.
