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
- **Environment Consistency Validator (`validate_environment_consistency`)**:
  - Enforces 1-to-1 mapping: `dev` -> `development`, `test` -> `development`, `staging` -> `staging`, `prod` -> `production`.
  - Emits backward-compatible `"Production requires ENV=prod"` exception on mismatched configs.
- **Hosted Fail-Fast Invariants (`_fail_fast()`)**:
  - Staging requires `REPO_BACKEND=sql`, `STORAGE_BACKEND=s3`, `S3_BUCKET`, `AUTH_MODE=jwks` + `AUTH_JWKS_URL`, non-empty non-wildcard CORS, and valid S3 credentials or IAM role.
  - Production enforces all staging invariants plus: `TRYON_PROVIDER` cannot be `mock` (Rule I08), cannot be unimplemented `fashn_selfhost`, mandatory `PRIVACY_URL` and `TERMS_URL`, all CORS origins must use `https://`, non-empty `FASHX_RETAILER_ALLOWED_HOSTS`, and `ENABLE_B2B=False` for MVP.

### B. IAM Role Storage Support (`backend/fashx/core/dependencies.py`)
- Enhanced `get_storage()` to support `S3_USE_IAM_ROLE=true`:
  - When enabled, `key_id` and `secret` are set to `None`, directing boto3 to the default AWS credential chain (ECS Task Role / IRSA / OIDC), eliminating static access keys in hosted deployments.

### C. Hosted Startup Gate (`backend/fashx/main.py`)
- Added hosted environment validation inside `create_app()`:
  - When `settings.is_hosted` is True, `validate_release_config(settings.to_release_config())` is invoked during app factory execution, halting startup if any stage invariant is violated.

---

## 3. Verification & Testing

1. **New Comprehensive Test Suite (`tests/core/test_environment_settings.py`)**:
   - 20 unit tests covering default local configurations, dev/test/staging/prod configurations, environment mismatches, staging refusal invariants, production refusal invariants, and `create_app` startup validation.
   - Output: `20 passed in 4.33s`.
2. **Existing Settings Test Suites**:
   - `tests/unit/test_settings.py` and `tests/unit/test_settings_prod_refusal.py`: `11 passed in 3.20s`.
   - `tests/unit/test_rc08_release_config.py`: `13 passed in 3.16s`.
3. **Static Quality Gates**:
   - `ruff check`: All checks passed.
   - `mypy`: Success, no issues found in source files.
   - `docs_lint.py`: docs lint ok.
