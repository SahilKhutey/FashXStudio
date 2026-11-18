# Source Types and Access Methods Specification

**Workstream**: 5.1.4 — Source Types & Technical Access Methods  
**Status**: Active  
**Module**: `backend/fashx/catalog/adapters/`

---

## 1. Supported Source Types

| Source Type Enum | Primary Use Case | Ingestion Pattern | Typical Latency |
|---|---|---|---|
| `MERCHANT_API` | Direct enterprise merchant REST / GraphQL integration | Scheduled pull / real-time webhook | Real-time / Hourly |
| `AFFILIATE_API` | Affiliate network product APIs (e.g., CJ, Rakuten, Impact) | Paginated catalog sync | Daily |
| `MERCHANT_FEED` | Bulk product data feeds (CSV, TSV, XML, JSONL) | Scheduled batch download | Daily / Nightly |
| `PARTNER_EXPORT` | Ad-hoc or offline negotiated brand exports | Secure SFTP / S3 file drop | Weekly / Monthly |
| `SHOPIFY_APP` | Direct Shopify merchant app store integration | Webhook + Admin GraphQL API | Near real-time |
| `OTHER_AUTHORIZED` | Custom enterprise bilateral integrations | Bespoke adapter | Negotiated |

---

## 2. Technical Access Methods & Credential Security

Every access method connects via securely stored credentials. Raw credentials, API tokens, client secrets, and private keys MUST NEVER be stored in the database or logs. Only the ARN or path (`credential_secret_ref`) is recorded.

### 1. `OAUTH2`
- **Protocol**: OAuth 2.0 Client Credentials Grant (RFC 6749) or Authorization Code Flow.
- **Credential Storage**: Client ID, Client Secret, Token URL stored in AWS Secrets Manager.
- **Token Management**: In-memory token cache with proactive refresh 5 minutes prior to expiration.

### 2. `API_KEY`
- **Protocol**: HTTP Header `Authorization: Bearer <token>` or `X-API-Key: <token>`.
- **Credential Storage**: Key stored in AWS Secrets Manager.
- **Rotation**: Dual-key support for seamless rotation without downtime.

### 3. `SIGNED_REQUEST`
- **Protocol**: HMAC-SHA256 request signing using merchant-issued secret and timestamp header.
- **Clock Drift**: Requests validated with maximum 300-second timestamp tolerance.

### 4. `HTTPS_FEED`
- **Protocol**: Authenticated HTTPS GET / POST over TLS 1.3.
- **Authentication**: Basic Auth or Bearer Token via secure HTTP headers.

### 5. `SFTP`
- **Protocol**: SSH File Transfer Protocol (Port 22) with ED25519 or RSA-4096 key pair.
- **Storage**: Private keys managed via AWS Secrets Manager.

### 6. `MANUAL_PARTNER_EXPORT`
- **Protocol**: Pre-signed S3 bucket upload with bucket policy restricting upload to merchant's CIDR block.

---

## 3. Rate Limiting and Circuit Breaker Architecture
Every adapter derives from `PermissionAwareAdapter` and integrates:
1. **Rate Limiter**: Token-bucket algorithm strictly enforcing `max_rps` per source.
2. **Circuit Breaker**: Trips to `OPEN` state after 5 consecutive failures, backing off for configured cooldown interval (default 300s) before attempting `HALF_OPEN` canary probes.
3. **Authorization Pre-Check**: Before initiating any network request, the adapter invokes `CatalogAuthorizationGuard` to verify `PRODUCT_DATA_READ`.
