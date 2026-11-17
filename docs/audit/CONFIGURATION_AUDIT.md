# FashXStudio — Phase 02.4: Configuration Audit

**Document ID:** `FASHX-AUD-005`  
**Phase:** 02.4 — Audit Mock Versus Real Integrations (Execution A)  
**Date:** 2026-11-11  
**Author:** Antigravity Agent (Auditor)  
**Status:** COMPLETE (Audited Baseline)  
**Branch:** `recovery/rc13.1-governance-correction`  

---

## 1. Executive Summary

This configuration audit documents the environment variable configuration, effective application settings, and fail-fast validation gates governing FashXStudio. In conformance with repository governance rules (**Rule 2** and **Rule 8**), all findings reflect real command executions performed on the local checkout. No secret values, private keys, or credentials have been printed or committed.

The key finding of this audit is:
> **The current local development configuration is fully functional for local development and offline testing, but operates entirely in mock and local fallback modes.** In accordance with repository design, production execution is gated by a hard fail-fast validator (`Settings._fail_fast()`) that strictly refuses mock dependencies, local storage, local JWTs, and memory repositories when `ENV=prod` or `APP_ENV=production`.

---

## 2. Environment Variable Audit (Safe Presence Inspection)

The following 26 environment variables govern external integrations, storage, security, and persistence across FashXStudio:

```powershell
$envNames = @(
  "ENV","APP_ENV","TRYON_PROVIDER","FASHN_API_KEY","FASHN_BASE_URL",
  "FASHN_MODEL","TRYON_TIMEOUT_S","TRYON_MAX_ATTEMPTS","VLM_PROVIDER",
  "ANTHROPIC_API_KEY","AUTH_MODE","AUTH_ISSUER","AUTH_AUDIENCE",
  "AUTH_JWKS_URL","SUPABASE_URL","SUPABASE_SECRET_KEY","STORAGE_BACKEND",
  "S3_BUCKET","S3_ENDPOINT_URL","S3_REGION","S3_ACCESS_KEY_ID",
  "S3_SECRET_ACCESS_KEY","S3_USE_IAM_ROLE","DATABASE_URL","REDIS_URL","REPO_BACKEND"
)
```

### Empirical Inspection Output:
```
ENV = (not set; repository default may apply)
APP_ENV = (not set; repository default may apply)
TRYON_PROVIDER = (not set; repository default may apply)
FASHN_API_KEY = NOT SET
FASHN_BASE_URL = (not set; repository default may apply)
FASHN_MODEL = (not set; repository default may apply)
TRYON_TIMEOUT_S = (not set; repository default may apply)
TRYON_MAX_ATTEMPTS = (not set; repository default may apply)
VLM_PROVIDER = (not set; repository default may apply)
ANTHROPIC_API_KEY = NOT SET
AUTH_MODE = (not set; repository default may apply)
AUTH_ISSUER = (not set; repository default may apply)
AUTH_AUDIENCE = (not set; repository default may apply)
AUTH_JWKS_URL = (not set; repository default may apply)
SUPABASE_URL = (not set; repository default may apply)
SUPABASE_SECRET_KEY = NOT SET
STORAGE_BACKEND = (not set; repository default may apply)
S3_BUCKET = (not set; repository default may apply)
S3_ENDPOINT_URL = (not set; repository default may apply)
S3_REGION = (not set; repository default may apply)
S3_ACCESS_KEY_ID = NOT SET
S3_SECRET_ACCESS_KEY = NOT SET
S3_USE_IAM_ROLE = (not set; repository default may apply)
DATABASE_URL = (not set; repository default may apply)
REDIS_URL = (not set; repository default may apply)
REPO_BACKEND = (not set; repository default may apply)
```

---

## 3. Local `.env` File Inspection (Safe Key Audit)

The repository root contains a local `.env` file. Safe key enumeration (without printing secret values) revealed the following configured keys:

```
APP_ENV
ENV
APP_NAME
APP_VERSION
LOG_LEVEL
CORS_ORIGINS
DATABASE_URL
REDIS_URL
READINESS_REQUIRES_DATABASE
SENTRY_DSN
SENTRY_ENVIRONMENT
FASHX_ENABLE_FROZEN
AUTH_MODE
AUTH_ISSUER
AUTH_AUDIENCE
AUTH_JWT_SECRET
AUTH_JWKS_URL
```

**Notable Absences:**
- Neither `FASHN_API_KEY` nor `ANTHROPIC_API_KEY` is defined in `.env`.
- Neither `S3_BUCKET`, `S3_ACCESS_KEY_ID`, nor `S3_SECRET_ACCESS_KEY` is defined in `.env`.
- Neither `SUPABASE_URL` nor `SUPABASE_SECRET_KEY` is defined in `.env`.

---

## 4. Effective Application Settings

Invoking the Pydantic Settings factory (`backend/fashx/core/settings.py`) yields the following effective runtime configuration:

```powershell
python -c "from fashx.core.settings import get_settings; s=get_settings(); print({'env':s.env,'app_env':s.app_env,'tryon_provider':s.tryon_provider,'fashn_key_configured':bool(s.fashn_api_key and s.fashn_api_key.get_secret_value()),'fashn_base_url':s.fashn_base_url,'fashn_model':s.fashn_model,'vlm_provider':s.vlm_provider,'auth_mode':s.auth_mode,'auth_issuer':s.auth_issuer,'auth_audience':s.auth_audience,'jwks_url_configured':bool(s.auth_jwks_url),'supabase_url_configured':bool(s.supabase_url),'supabase_secret_configured':bool(s.supabase_secret_key and s.supabase_secret_key.get_secret_value()),'storage_backend':s.storage_backend,'s3_bucket':s.s3_bucket,'repo_backend':s.repo_backend})"
```

### Empirical Output:
```json
{
  "env": "dev",
  "app_env": "development",
  "tryon_provider": "mock",
  "fashn_key_configured": false,
  "fashn_base_url": "https://api.fashn.ai/v1",
  "fashn_model": "tryon-v1.6",
  "vlm_provider": "mock",
  "auth_mode": "local",
  "auth_issuer": "fashx-local",
  "auth_audience": "fashx-api",
  "jwks_url_configured": false,
  "supabase_url_configured": false,
  "supabase_secret_configured": false,
  "storage_backend": "local",
  "s3_bucket": null,
  "repo_backend": "memory"
}
```

---

## 5. Production Refusal Gates (`_fail_fast`)

The repository enforces production readiness at the Pydantic model validation layer (`backend/fashx/core/settings.py:152-185`). When `is_production` is true (`ENV=prod` or `APP_ENV=production`), the application refuses to start if any of the following conditions are violated:

1. **Environment Consistency:** `ENV` must equal `"prod"`.
2. **Persistence Backend:** `REPO_BACKEND` must equal `"sql"`. Memory repositories are rejected with: `"prod requires REPO_BACKEND=sql"`.
3. **Object Storage Backend:** `STORAGE_BACKEND` must equal `"s3"`. Local storage is rejected with: `"prod requires STORAGE_BACKEND=s3"`.
4. **S3 Bucket Configuration:** `S3_BUCKET` must be set; credentials (`S3_ACCESS_KEY_ID` + `S3_SECRET_ACCESS_KEY`) or `S3_USE_IAM_ROLE=true` must be present.
5. **Authentication Mode:** `AUTH_MODE` must equal `"jwks"` and `AUTH_JWKS_URL` must be non-empty. Local JWT auth is rejected with: `"prod requires AUTH_MODE=jwks and AUTH_JWKS_URL"`.
6. **VTO Provider Clearance:** `TRYON_PROVIDER` cannot be `"mock"`. Rejected with: `"prod requires non-mock TRYON_PROVIDER (rule I08)"`.
7. **Legal URLs:** `PRIVACY_URL` and `TERMS_URL` must both be configured.
8. **Security Policies:** Wildcard CORS (`"*"`) is strictly prohibited; `FASHX_RETAILER_ALLOWED_HOSTS` must not be empty.
9. **Feature Scope:** `ENABLE_B2B` must be `False` for the initial consumer MVP.
