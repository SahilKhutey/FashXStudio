# Environment Configuration and Secret Management Standard

**Status:** Adopted
**Version:** 1.0
**Effective Date:** 2026-11-11
**Category:** Engineering Configuration

---

## 1. Purpose and Scope

This standard defines the rules for environment classification, configuration precedence, secret handling, and fail-fast startup validation for FashXStudio. Centralizing configuration and protecting secrets prevents configuration drift, accidental disclosure of credentials, and security misconfigurations in production.

All backend configuration is defined centrally in:
```text
backend/fashx/core/settings.py
```
using Pydantic Settings (`BaseSettings`).

---

## 2. Environment Classification

FashXStudio defines exactly three operational environment classes:

| Environment (`ENV`) | Description | Data & Service Tier |
|---|---|---|
| `dev` | Local developer machine | In-memory or local PostgreSQL, mock VTO, local storage |
| `test` | Automated CI test runners | Ephemeral PostgreSQL (`pgvector`), test Redis, mock external providers |
| `prod` | Production deployment | Managed PostgreSQL, AWS S3 storage, real VTO provider, JWKS auth |

> **Note:** `APP_ENV` may continue to store application lifecycle labels (`development`, `staging`, `production`), but the primary system behavior switch is controlled strictly by `ENV`.

---

## 3. Configuration Precedence

Configuration values resolve in strict hierarchical order:

```text
1. Operating System Environment Variables (Highest Precedence)
       ↓
2. Local .env File (Ignored by git; developer overrides)
       ↓
3. Application Defaults in Pydantic Settings (Lowest Precedence; Safe Defaults Only)
```

No secret, password, or production credential may ever be embedded in application default values or committed code.

---

## 4. Ten Core Configuration Rules

1. **Pydantic Settings Mandatory:** All backend environment variables must be formally declared in `backend/fashx/core/settings.py` with explicit types and field descriptions.
2. **No Hardcoded Credentials:** Never hardcode passwords, API keys, tokens, or encryption keys in source files.
3. **Secret Protection with `SecretStr`:** All secrets must be typed as `pydantic.SecretStr` to prevent accidental string casting, logging, or serialization.
4. **Gitignore `.env`:** The `.env` file must always be listed in `.gitignore`. Never commit a `.env` file to version control.
5. **Safe Placeholders in `.env.example`:** The committed `.env.example` file must contain only non-secret placeholders and safe documentation defaults.
6. **Production Fail-Fast Validation:** If any mandatory configuration is missing in `prod` (e.g., `S3_BUCKET_NAME`, `FASHN_API_KEY`, `AUTH_JWKS_URL`), the service must immediately fail startup with a descriptive error.
7. **Database Isolation:** Test databases must be completely separated from development and production databases. Automated tests must never run against development or production databases.
8. **Production Mock Prohibition:** In `prod`, settings validators must strictly reject `TRYON_PROVIDER=mock`, `STORAGE_BACKEND=local`, or `REPO_BACKEND=memory`.
9. **Explicit CORS Allowlist:** Production CORS configurations must specify explicit, HTTPS-approved domain origins. Wildcard `*` origins are strictly forbidden in production.
10. **Zero Secrets in Diagnostics:** Diagnostic endpoints (`/health`, `/metrics`, debug logs) must never output active configuration values or decrypted secrets.

---

## 5. Reference `.env.example`

Below is the standard reference configuration template for local development:

```bash
# Application Lifecycle
ENV=dev
APP_ENV=development
APP_NAME=FashXStudio API
APP_VERSION=0.1.0
LOG_LEVEL=INFO

# Backend Infrastructure
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fashx_dev
REDIS_URL=redis://localhost:6379/0

# Authentication & Identity
AUTH_MODE=local
AUTH_ISSUER=fashx-local
AUTH_AUDIENCE=fashx-api
AUTH_JWT_SECRET=REPLACE_WITH_LOCAL_TEST_SECRET_32_CHARS_MINIMUM

# Storage & Repository Backends
REPO_BACKEND=memory
STORAGE_BACKEND=local
LOCAL_STORAGE_DIR=./.local_storage

# Virtual Try-On (VTO)
TRYON_PROVIDER=mock
TRYON_ENABLED=true
FASHN_API_KEY=

# Vision-Language Model (VLM)
VLM_PROVIDER=mock

# Feature Flags
ENABLE_B2B=false
FASHX_ENABLE_FROZEN=false

# Observability & Monitoring
SENTRY_DSN=
SENTRY_ENVIRONMENT=development
```

---

## 6. Production Safeguards and Secret Storage

For staging and production deployments:
- Configuration and secrets must be injected through container environment variables or managed secrets managers (e.g., AWS Secrets Manager, HashiCorp Vault, Doppler).
- Never transmit production credentials, database URLs, or API keys over unencrypted communication channels, issue trackers, pull requests, or chat interfaces.
