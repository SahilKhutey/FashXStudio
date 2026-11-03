# RC-03 — Scope & Boundaries

## Mission Statement
The primary objective of **RC-03** is to integrate the reconstructed mobile frontend screens (from RC-02) with the recovered backend services (from RC-01) into a secure, cohesive, verified consumer application.

## Non-Goals & Boundaries
1. **No Total Backend Rewrite**: We preserve existing clean architecture routers, repositories, and domain services.
2. **No Real GPU Model Deployment**: Mock VTO mode with `"PREVIEW ONLY"` watermark remains standard in local and CI environments.
3. **Frozen Commerce Boundaries (ADR-0001)**: FashX does not handle checkout, payment processing, or order fulfillment directly. All commerce transactions route via affiliate redirect URLs.
4. **Documentation Rules (AGENTS.md)**:
   - Never edit `docs/evidence/`, `docs/provenance.md`, or `docs/release/gates.md`.
   - Never write simulated results, numbers, or verdicts without pasting real command outputs.
   - Never mark rows ✅ in status docs (use 🟢 or 🟡).
   - Never weaken CI gates or add ignores.

## Deliverables Checklist
- [x] **D03.1 Identity & Query Isolation**: Centralized query keys with user isolation, clearing cache on sign-out/account switch.
- [x] **D03.2 Safe Shopping Redirects**: Security helper `isSafeRetailerRedirect` preventing open redirects and untrusted protocols.
- [x] **D03.3 Health Probes Consolidation**: Standardized `/healthz/live` and `/healthz/ready`.
- [x] **D03.4 Smoke Verification Script**: `scripts/rc03_smoke.py` validating 6 core workflows end-to-end.
- [x] **D03.5 OpenAPI Contract Snapshot**: Exported specification to `artifacts/rc03/openapi.json`.
- [x] **D03.6 E2E Integration Test Suite**: Pytest suite `tests/integration/test_rc03_e2e_integration.py`.
- [x] **D03.7 Complete Documentation**: 13 markdown records in `docs/reengineering/RC03/`.
