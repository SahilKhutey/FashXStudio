# Workstream 8.1: Build Product Size Data

## 1. Executive Summary

Workstream 8.1 establishes the foundational data layer for FashXStudio's fit intelligence platform. It provides a versioned, immutable size-data foundation that captures merchant-provided sizing information, respects regional sizing systems, normalizes measurement units with deterministic precision, enforces validation boundaries, tracks variant availability freshness, and exposes clear, fail-closed contracts for shoppers and client apps.

### Core Product Invariants
1. **No Hallucinated Size Charts**: FashXStudio never invents missing size charts or fills empty cells using generative AI. If a merchant has not provided a verified size chart, the product explicitly returns `UNAVAILABLE`.
2. **Strict Separation of Visual Try-On and Fit**: A visual try-on simulation shows drape and appearance; it is never presented as proof of physical fit. Sizing charts describe merchant dimensions, not personal sizing guarantees.
3. **No Unverified System Conversion**: Sizing systems (e.g. US, UK, EU, INTL) cannot be mapped to one another unless a verified conversion table is registered for that specific category and merchant. Unverified conversions retain native merchant size labels.
4. **Availability vs. Sizing Invariant**: A size chart row defines dimension standards; it does not imply that the variant is currently in stock. Variant availability is tracked via timestamped inventory snapshots.
5. **Durable Immutability**: All size chart edits create a new, numbered, content-fingerprinted revision. Historical revisions are never updated in place.

---

## 2. Deliverables Directory

| File | Title | Scope |
|---|---|---|
| [01-size-data-architecture.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/01-size-data-architecture.md) | Size Data Architecture | End-to-end domain model, state machines, and system interactions |
| [02-sizing-system-registry.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/02-sizing-system-registry.md) | Sizing System Registry | Sizing systems (US, UK, EU, INTL), proprietary systems, mapping rules |
| [03-measurement-field-definitions.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/03-measurement-field-definitions.md) | Measurement Field Definitions | Garment taxonomy measurement fields, range bounds, category constraints |
| [04-unit-normalization.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/04-unit-normalization.md) | Unit Normalization | Deterministic conversion formulas, Round Half-Up precision, finite checking |
| [05-validation-rules-and-quarantine.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/05-validation-rules-and-quarantine.md) | Validation & Quarantine | Validation rules, quarantine logging, and review workflows |
| [06-variant-availability-model.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/06-variant-availability-model.md) | Variant Availability Model | Variant inventory snapshots, staleness degradation to UNKNOWN |
| [07-fingerprint-and-versioning.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/07-fingerprint-and-versioning.md) | Fingerprinting & Versioning | SHA-256 canonical fingerprinting, immutable revision history, event audits |
| [08-merchant-ingestion-pipeline.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/08-merchant-ingestion-pipeline.md) | Ingestion Pipeline | Ingestion workflows, idempotency checks, quarantine handling |
| [09-shopper-api-specification.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/09-shopper-api-specification.md) | Shopper API Specification | REST API endpoints, query parameters, fail-closed responses |
| [10-mobile-ui-presentation.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/10-mobile-ui-presentation.md) | Mobile UI Presentation | React Native contracts, unit toggle, system labels, fit disclaimer |
| [11-security-and-isolation.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/11-security-and-isolation.md) | Security & Isolation | Tenant boundaries, private data isolation, input sanitization |
| [12-database-schema-and-migration.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/12-database-schema-and-migration.md) | Database Schema & Migration | Alembic migration 0056, 9 database tables, indexes, constraints |
| [13-test-catalogue.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/13-test-catalogue.md) | Test Catalogue | Test coverage mapping across unit, domain, integration, and e2e |
| [14-release-checklist.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/phase-08/8.1-product-size-data/14-release-checklist.md) | Release Readiness Checklist | Operational verification, production deployment gates, monitoring |
