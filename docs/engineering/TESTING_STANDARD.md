# Testing Standard

**Status:** Adopted
**Version:** 1.0
**Effective Date:** 2026-11-11
**Category:** Engineering Quality

---

## 1. Purpose and Scope

This standard defines the mandatory testing policies, test levels, execution commands, and priority classifications for FashXStudio. High test fidelity ensures that user privacy, virtual try-on stability, catalog ingestion, and multi-tenant security are maintained across all platform changes.

The testing stack reflects the repository's native technologies:
- **Backend:** Python 3.12, Pytest, Ruff, Mypy, SQLite (in-memory for unit tests), PostgreSQL with `pgvector` (for database integration tests), Redis.
- **Mobile:** React Native / Expo, Jest, React Native Testing Library, TypeScript, ESLint.

---

## 2. Test Levels

FashXStudio categorizes tests into ten distinct levels:

| Test Level | Scope and Purpose | Repository Examples |
|---|---|---|
| **1. Unit** | Pure function, domain logic, and utility testing in total isolation. No I/O or network. | Fit-score calculations, garment type classification, token parsing, string sanitization |
| **2. Component** | Single module or adapter boundary testing with mocked external dependencies. | S3 storage adapter with local memory backend, Fashn VTO adapter client parsing |
| **3. API / Contract** | HTTP request/response validation, schema contracts, error envelopes, and status codes. | `/api/v1/profile` schema validation, `/api/v1/tryons` error responses |
| **4. Integration** | Real interaction with backing infrastructure services. | SQLAlchemy repositories against PostgreSQL (`pgvector`), Celery/Redis queue workers |
| **5. Contract** | Upstream provider schema verification and mobile client OpenAPI synchronization. | Fashn API response fixtures, OpenAPI schema matching `mobile/src/api/schema.d.ts` |
| **6. Mobile** | Component rendering, user interaction, screen state, and navigation. | Onboarding carousel, camera permission request, wardrobe list, try-on progress screen |
| **7. End-to-End** | Full lifecycle flows crossing UI, API, database, and background processing. | User onboarding → photo upload → garment selection → VTO submission → wardrobe save |
| **8. Security** | Authorization gates, tenant isolation, and data exposure prevention. | Cross-user photo isolation, consent enforcement, prompt injection defense |
| **9. Performance** | Latency, throughput, query optimization, and memory benchmarks. | VTO polling queue load test, catalog search latency under vector index load |
| **10. Migration** | Schema upgrade and downgrade transitions against PostgreSQL. | Alembic upgrade to head, rollback -1, re-upgrade, schema check |

---

## 3. Minimum Testing Requirements for Every Code Change

Before opening or merging any Pull Request, engineers must ensure:

1. **New Tests for New Code:** Every new capability, API endpoint, or bug fix must have corresponding automated tests.
2. **Happy Path:** Test expected positive flows with realistic sample inputs.
3. **Invalid Inputs:** Test malformed payloads, out-of-range parameters, invalid image types, and missing fields.
4. **Authorization & Ownership:** Explicitly test that unauthorized users or mismatched owners are blocked (HTTP 401/403).
5. **Upstream Failures:** Test provider timeouts, network disconnections, 500 responses, and circuit-breaker behavior.
6. **Boundary Conditions:** Test minimum/maximum limits (e.g., maximum photo dimensions, empty lists, pagination edges).
7. **Persistence Verification:** When modifying models or repositories, verify data is accurately persisted and re-queried.
8. **No Silent Skips:** Never add `@pytest.mark.skip` or `xit()` without an explicit issue link and prior review approval.
9. **No Assertion Weakening:** Never relax assertions or remove existing checks to achieve a passing test run (`AGENTS.md` Rule 4).
10. **Transparent Reporting:** Report test skips or environment-blocked suites honestly (e.g., PostgreSQL or Docker unavailable locally).

---

## 4. Mandatory Test Execution Commands

### 4.1 Backend Commands

```bash
# 1. Fast unit test suite (excluding database and frozen modules)
python -m pytest tests/unit -q -m "not db and not frozen"

# 2. Database integration tests (requires PostgreSQL with pgvector)
python -m pytest tests -m db -q -rs

# 3. Full test suite (all non-frozen tests)
python -m pytest tests -q -p no:cacheprovider -m "not frozen"

# 4. Lint and style checks
python -m ruff check .

# 5. Static type checking
python -m mypy .
```

### 4.2 Mobile Commands

```bash
cd mobile

# 1. Jest unit and component tests
npx jest --ci

# 2. ESLint code quality checks
npx eslint . --max-warnings 0

# 3. TypeScript type checking
npx tsc --noEmit

# 4. Expo environment doctor
npx expo-doctor

# 5. Production bundle compilation verification (Hermes Android)
npx expo export --platform android

cd ..
```

### 4.3 Documentation and Release Gate Verification

```bash
# Validate documentation links and evidence cards
python scripts/docs_lint.py

# Full repository local verification gate (against PostgreSQL)
bash scripts/ci/local_gate.sh
```

A change is verified only if `scripts/ci/local_gate.sh` outputs:
```text
LOCAL GATE: ALL GREEN
```
or all checks in GitHub Actions CI are green.

---

## 5. Critical FashXStudio Test Priorities

Test coverage and test depth must align with platform criticality:

| Priority | Module / Subsystem | Required Verification Tests |
|---|---|---|
| **P0** | **Authentication & Identity** | Expired tokens, tampered signatures, missing authorization headers, user ID isolation |
| **P0** | **Profile & Consent** | Explicit consent gating, consent revocation, right-to-be-forgotten deletion workflows |
| **P0** | **Virtual Try-On (VTO)** | Provider timeouts, provider outages, job status state machine, image ownership |
| **P0** | **Object Storage** | Presigned URL expiration, private bucket access controls, cross-user photo access denial |
| **P0** | **Catalog Ingestion** | Provenance attribution, copyright flags, deduplication, corrupt feed handling |
| **P0** | **Database & Migrations** | PostgreSQL upgrade/downgrade cycles, foreign key cascade constraints, schema check |
| **P1** | **Discovery & Ranking** | Vector similarity ranking, fit-preference filtering, deterministic pagination |
| **P1** | **Wardrobe** | Save outfit, remove outfit, list outfits, user isolation |
| **P1** | **Analytics & Attribution** | Validated event schemas, checkout clickout attribution, no PII leakage |
| **P1** | **Merchant Multi-Tenancy** | Cross-tenant data isolation, inventory isolation, API key permissions |
| **P1** | **Mobile Experience** | Offline caching, network retry, graceful error recovery, camera permission denial |

---

## 6. Coverage Policy

FashXStudio does not enforce an arbitrary, repository-wide code coverage threshold that encourages low-quality test assertions. Instead:
1. The historical coverage baseline is captured and monitored.
2. Per-critical-module thresholds (e.g., P0 modules requiring 90%+ branch coverage) are introduced via formal Architectural Decision Records (ADRs).
3. Reviewers must require thorough positive, negative, and edge-case tests for all P0/P1 components regardless of overall line coverage metrics.
