# RC13: Technical Validation & Infrastructure

## 1. Scope & Verification Criteria
The technical validation track evaluates backend and client infrastructure:
- **Backend API Server**:
  - FastAPI endpoints healthy (`/health`, `/health/ready`).
  - Database connectivity: PostgreSQL with `pgvector` extension.
  - Migration verification: Alembic clean upgrade and downgrade cycle.
- **Client App (React Native / Expo)**:
  - TypeScript type checking clean (`npx tsc --noEmit`).
  - Mobile smoke test suites passing.
  - Zero unhandled fatal crashes; target >= 99% crash-free sessions.
- **Automated Test Coverage**:
  - RC08–RC13 test suites green.
  - Zero skipped tests without explicit documented justification.

## 2. Gate Alignment: G1 & G2
- **G1 (Automated Test & Build)**:
  - Requires clean CI run across backend, mobile, and security tests.
- **G2 (Staging Database & Cloud Services)**:
  - Requires successful execution of PostgreSQL migration and cloud readiness audits.

## 3. Evidence Collection Protocol
- To verify G1: Founder runs test suite and CI workflow, records log output in an authentic evidence card.
- To verify G2: Founder executes migration verification against live Postgres instance (`alembic upgrade head; downgrade -1; upgrade head`).
