> **Development log. Contains no real-world measurements or simulated evidence. Pre-pilot status maintained per AGENTS.md.**

# Dev Log: Phase 03.1 — Production Infrastructure and Backend Integration: Define Environments

**Branch**: `recovery/rc13.1-governance-correction`
**Milestone Scope**: Phase 03 — Production Infrastructure and Backend Integration (Section 3.1: Define Environments)
**Date**: November 12, 2026
**Status**: Completed & Verified Locally

---

## 1. Context & Architectural Motivation

Phase 01 established the validated product strategy, shopper and merchant user journeys, and MVP boundaries. Phase 02 completed the comprehensive codebase audit and established the engineering standards.

Phase 03 initiates the production infrastructure and backend integration workstream. Section 3.1 establishes the controlled four-environment architecture:
1. **Local**: Individual engineer development, local automated testing, synthetic mock datasets, developer workstation or local Docker.
2. **Shared Development**: Multi-developer feature branch integration, shared cloud deployment, synthetic test fixtures.
3. **Staging**: Release candidate validation, production-mirroring security guardrails, private S3 storage, JWKS token verification, pre-pilot qualification.
4. **Production**: Live shoppers and merchants, multi-AZ deployment, strict HTTPS CORS, real VTO provider inference, zero mock services.

### The Governing Infrastructure Separation Invariant
> Code may move freely between environments through automated release promotion. Databases, user personal data, biometric/clothing photos, credentials, and environment-specific resources must never be copied, bridged, or shared casually between them.

---

## 2. Technical Implementation Highlights

### A. Environment Configuration & Settings Hardening (`backend/fashx/core/settings.py`)
- **Strict Typing for Environments**:
  - `Environment = Literal["dev", "test", "staging", "prod"]`
  - `ApplicationEnvironment = Literal["development", "staging", "production"]`
- **Helper Predicates**:
  - `is_production`: True when `ENV == "prod"` or `APP_ENV == "production"`.
  - `is_staging`: True when `ENV == "staging"` or `APP_ENV == "staging"`.
  - `is_hosted`: True when either `is_staging` or `is_production`.
- **Database Pool & CA Configuration**:
  - `db_pool_size`: Configurable per environment (default: 5).
  - `db_max_overflow`: Configurable per process (default: 5).
  - `db_pool_timeout_s`: Database connection acquisition timeout (default: 20s).
  - `db_ssl_ca_file`: Path to RDS global certificate authority bundle (default: `None`, `/etc/ssl/certs/aws-rds-global-bundle.pem` in container).
- **Environment Consistency Validator (`validate_environment_consistency`)**:
  - Enforces 1-to-1 mapping: `dev` -> `development`, `test` -> `development`, `staging` -> `staging`, `prod` -> `production`.
  - Emits backward-compatible `"Production requires ENV=prod"` exception on mismatched configs.
- **Hosted Fail-Fast Invariants (`_fail_fast()`)**:
  - Staging requires `REPO_BACKEND=sql`, `STORAGE_BACKEND=s3`, `S3_BUCKET`, `AUTH_MODE=jwks` + `AUTH_JWKS_URL`, non-empty non-wildcard CORS, and valid S3 credentials or IAM role. Rejects static S3 credentials when `S3_USE_IAM_ROLE=True`.
  - Production enforces all staging invariants plus: `TRYON_PROVIDER` cannot be `mock` (Rule I08), cannot be unimplemented `fashn_selfhost`, mandatory `PRIVACY_URL` and `TERMS_URL`, all CORS origins must use `https://`, non-empty `FASHX_RETAILER_ALLOWED_HOSTS`, and `ENABLE_B2B=False` for MVP.

### B. Database TLS Context & Connection Pooling (`backend/fashx/core/database.py`)
- Configured `get_engine()` with verified SSL context using `ssl.create_default_context(cafile=settings.db_ssl_ca_file)` when `db_ssl_ca_file` is specified.
- Applied `db_pool_size`, `db_max_overflow`, and `db_pool_timeout_s` to the asynchronous PostgreSQL engine.

### C. Container Hardening with Amazon RDS CA Bundle (`Dockerfile`)
- Updated the final runtime stage of `Dockerfile`:
  - Installed `ca-certificates` and `curl`.
  - Downloaded Amazon RDS global CA bundle: `https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem` into `/etc/ssl/certs/aws-rds-global-bundle.pem`.
  - Set default environment variable: `ENV DB_SSL_CA_FILE=/etc/ssl/certs/aws-rds-global-bundle.pem`.

### D. IAM Role Storage Support (`backend/fashx/core/dependencies.py`)
- Enhanced `get_storage()` to support `S3_USE_IAM_ROLE=true`:
  - When enabled, `key_id` and `secret` are set to `None`, directing boto3 to the default AWS credential chain (ECS Task Role / IRSA / OIDC), eliminating static access keys in hosted deployments.

### E. Hosted Startup Gate (`backend/fashx/main.py`)
- Added hosted environment validation inside `create_app()`:
  - When `settings.is_hosted` is True, `validate_release_config(settings.to_release_config())` is invoked during app factory execution, halting startup if any stage invariant is violated.

### F. Terraform S3 Media Storage Module (`infra/aws/rds/storage.tf`)
- Codified 3 private S3 buckets (`fashx-dev-private-ACCOUNTID`, `fashx-staging-private-ACCOUNTID`, `fashx-prod-private-ACCOUNTID`).
- Enforced Public Access Block on all 4 controls.
- Configured BucketOwnerEnforced ownership controls.
- Enforced AES256 server-side encryption.
- Attached bucket policy denying unencrypted transport (`aws:SecureTransport = false`).
- Configured lifecycle policies: 7-day multipart upload abort and 7-day expiration for `temporary/` prefix.

### G. Operational Scripts (`scripts/db/` & `scripts/release/`)
- `scripts/db/publish_database_url_secret.sh`: Queries RDS instance endpoint, fetches credentials from Secrets Manager, and publishes `postgresql+asyncpg://` connection URL to `/fashx/${ENV}/postgres/database-url`.
- `infra/aws/ecs/bootstrap.sh`: Creates ECS clusters (`fashx-dev`, `fashx-staging`, `fashx-prod`) with Container Insights and initializes CloudWatch log groups for `api`, `tryon`, `ingest`, `beat`, `migration` with 30-day retention.
- `scripts/release/promote_ecs.sh`: Resolves immutable ECR image digest from commit SHA tag, runs migration task definition, updates `api`, `tryon`, `ingest`, and `beat` services with deployment circuit breaker (`enable=true,rollback=true`), and validates `/healthz/live` and `/healthz/ready`.

### H. GitHub Actions Workflows (`.github/workflows/`)
- `.github/workflows/build-release.yml`: Build-once workflow that compiles immutable Docker image, tags with `sha-${{ github.sha }}`, pushes to ECR, and records image digest.
- `.github/workflows/promote.yml`: Promotion workflow triggered via `workflow_dispatch` targeting `development`, `staging`, or `production` with protected GitHub Environment approvals.

### I. ECS Task Definition Templates (`infra/aws/ecs/task-definitions/`)
- Codified parameterized task definition JSON templates for `api`, `tryon`, `ingest`, `beat`, and `migration`.

### J. Infrastructure Test Suites (`tests/core/` & `tests/infrastructure/`)
- `tests/core/test_deployment_environments.py`: 9 unit tests verifying staging/prod settings, `db_ssl_ca_file`, release config validation, and static credential rejection.
- `tests/core/test_environment_settings.py`: 20 unit tests verifying environment consistency and rejection of dev/test bypasses in hosted modes.
- `tests/core/test_s3_storage_iam.py`: 3 unit tests verifying that IAM role configuration sets credentials to `None` for the boto3 credential chain.
