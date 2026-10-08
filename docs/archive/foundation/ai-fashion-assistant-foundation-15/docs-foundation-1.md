# AI Fashion Assistant — Production Build Foundation 1

**Version:** 1.0  
**Date:** September 2026  
**Scope:** Shared domain contracts + production-shaped database foundation.

## Objective

Foundation 1 converts the architecture decisions into a stable contract/data layer without implementing product behavior.

## Implemented

- Versioned shared Pydantic contracts under `/schemas`.
- Separate identity, profile, catalog, recommendation, try-on, wardrobe, commerce, feedback, and event contracts.
- SQLAlchemy 2.x models under `/database/models`.
- Domain ownership reflected in separate table clusters.
- Merchant Product vs Canonical Garment vs Merchant Offer separation.
- Image-level content hashes instead of garment-level unique image hashes.
- Measurement provenance and confidence fields.
- Version-aware Try-On jobs and artifacts.
- Idempotency key separated from deterministic artifact key.
- Fit feedback separated from physical garment measurements.
- Visual try-on feedback separated from physical fit feedback.
- Domain-event persistence foundation.
- Alembic migration `0002_domain_foundation`.
- Contract and model foundation tests.

## Explicit non-goals

- Authentication implementation.
- Catalog ingestion implementation.
- Recommendation algorithms.
- Try-on model execution.
- Merchant integrations.
- Mobile feature screens.

## Acceptance criteria

1. Shared contracts can be imported without service-specific dependencies.
2. Database models load into one SQLAlchemy metadata registry.
3. Migration chain is `0001_foundation -> 0002_domain_foundation`.
4. Try-On idempotency and artifact uniqueness are database-enforced.
5. Domain ownership is visible in the table model.
6. Unit tests validate the contract/model baseline.
