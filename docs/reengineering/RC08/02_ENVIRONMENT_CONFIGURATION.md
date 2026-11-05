# RC08 — Environment Configuration

## 1. Environment Matrix

| Dimension | Development | Staging | Production |
|---|---|---|---|
| `APP_ENV` | `development` | `staging` | `production` |
| `ENV` | `dev` | `prod` | `prod` |
| `AUTH_MODE` | `local` | `jwks` | `jwks` |
| `AUTH_ISSUER` | `fashx-local` | `https://<ref>.supabase.co/auth/v1` | `https://auth.fashx.com` |
| `AUTH_AUDIENCE` | `fashx-api` | `authenticated` | `authenticated` |
| `DATABASE_URL` | Local Postgres / SQLite | Hosted PostgreSQL 16 (TLS required) | Hosted PostgreSQL 16 Multi-AZ |
| `REDIS_URL` | `redis://localhost:6379/0` | `rediss://staging-redis...` (TLS) | `rediss://prod-redis...` (TLS) |
| `STORAGE_BACKEND`| `local` / `s3` | `s3` (Dedicated staging bucket) | `s3` (Encrypted production bucket) |
| `TRYON_PROVIDER` | `mock` / `fashn_api` | `mock` / `fashn_api` (controlled) | `fashn_api` (approved real vendor) |
| `CORS_ORIGINS` | `["http://localhost:8081"]` | `["https://staging.fashx.com"]` | `["https://app.fashx.com"]` |
| `DEBUG` | `true` | `false` | `false` |

## 2. Release Configuration Validation
Release validation is enforced programmatically in `backend/fashx/core/release_config.py` via `validate_release_config(config)`:

1. **Staging & Production Invariants**:
   - `debug=False` enforced.
   - `auth_mode="jwks"` required.
   - `storage_backend="s3"` required (no local filesystem storage in release).
   - No wildcard `"*"` allowed in `cors_origins`.
   - All CORS origins must be well-formed HTTPS URLs in production.
2. **Production-Only Invariants**:
   - `tryon_provider="mock"` is strictly forbidden.
   - S3 bucket and credentials or IAM role attachment required.
   - Privacy and Terms URLs must be configured.
   - `ENABLE_B2B=false` enforced for MVP.
