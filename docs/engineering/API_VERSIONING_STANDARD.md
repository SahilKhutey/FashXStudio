# API Versioning and Evolution Standard

**Status:** Adopted
**Version:** 1.0
**Effective Date:** 2026-11-11
**Category:** Engineering Architecture

---

## 1. Purpose and Scope

This standard governs the design, versioning, evolution, and deprecation of all public and mobile-facing HTTP APIs in FashXStudio. A predictable API evolution policy ensures that updates to the backend do not disrupt mobile applications or external merchant integrations.

---

## 2. Versioning Strategy: URI Major Versioning

FashXStudio uses explicit URI path versioning for all application endpoints:

```text
/api/v1/...
/api/v2/...
```

### Versioning Rules

1. **Mandatory `/api/v1` Prefix:** All new public application routes must be mounted under `/api/v1`.
2. **Unversioned System Endpoints:** Operational and health-check endpoints remain unversioned at the root (e.g., `/health`, `/healthz`, `/metrics`).
3. **Major Version Increments:** A new major URI version (e.g., `/api/v2`) is required **only** when introducing breaking changes that cannot be achieved backward-compatibly.
4. **Additive Changes:** Backward-compatible changes must be added directly to the existing active version (`/api/v1`) without bumping the version number.
5. **No Silent Semantic Shifts:** Never change the semantic meaning, units, or data type of an existing field without introducing a new field name or major version.
6. **Deprecation Period:** Response fields or endpoints must not be removed without a documented deprecation schedule and client migration window.
7. **Decoupled Versioning:** API major versions are completely decoupled from internal microservice versions, database migration revision IDs, and mobile app release numbers.

---

## 3. Backward-Compatible vs. Breaking Changes

### Backward-Compatible Changes (Permitted in `/api/v1`)

- Adding a new optional request field (with a sensible default).
- Adding a new response field (clients must be built to ignore unknown fields).
- Adding a new API endpoint.
- Adding a new optional query parameter.
- Adding a new error code to an existing enum, provided standard error handling holds.
- Expanding rate limits or payload limits.

### Breaking Changes (Requires `/api/v2` or Formal RFC)

- Removing or renaming an existing response field.
- Changing a field's type (e.g., string to object, integer to float, scalar to array).
- Converting an optional request field into a required request field.
- Changing authentication mechanisms or required authorization scopes.
- Changing pagination semantics (e.g., offset/limit to cursor-based).
- Altering the HTTP response status code for an established outcome.
- Changing the schema of the public error envelope.

---

## 4. Standard Endpoint Structure

All resource-oriented routes should follow RESTful conventions:

```text
# Garment / Product Catalog
GET    /api/v1/products              # List / search products
GET    /api/v1/products/{product_id} # Retrieve product details

# Virtual Try-On
POST   /api/v1/tryons                # Submit virtual try-on job
GET    /api/v1/tryons/{job_id}       # Poll job status / retrieve result
DELETE /api/v1/tryons/{job_id}       # Cancel / delete try-on job

# Wardrobe
GET    /api/v1/wardrobe              # List saved outfits
POST   /api/v1/wardrobe              # Save outfit to wardrobe
DELETE /api/v1/wardrobe/{item_id}    # Remove outfit from wardrobe

# Profile & Consent
GET    /api/v1/profile               # Retrieve user profile and consent state
PUT    /api/v1/profile               # Update profile preferences
POST   /api/v1/profile/consent       # Record explicit biometric consent
POST   /api/v1/profile/consent/revoke# Revoke consent and trigger data purge
```

---

## 5. OpenAPI and Mobile Client Contract Synchronization

The mobile application relies on generated TypeScript definitions derived from the backend OpenAPI specification. Whenever an API schema changes, the contracts must be synchronized and verified:

```bash
# 1. Provide mock JWT secret for local schema generation
$env:AUTH_JWT_SECRET = "local-test-jwt-secret-key-32-chars-minimum"

# 2. Export the current OpenAPI specification from FastAPI
python -c "import json; from fashx.main import app; open('openapi.json', 'w').write(json.dumps(app.openapi(), indent=2))"

# 3. Generate TypeScript types for the mobile codebase
npx -y openapi-typescript openapi.json -o mobile/src/api/schema.generated.d.ts

# 4. Compare generated types against the committed schema
git diff --no-index mobile/src/api/schema.d.ts mobile/src/api/schema.generated.d.ts
```

> **Important:** Never blindly overwrite `mobile/src/api/schema.d.ts` to suppress a diff. Review each schema change, update the mobile client implementation, and verify that mobile unit tests pass before committing.
