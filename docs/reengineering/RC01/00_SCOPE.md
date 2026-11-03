# RC-01 — Scope & Deliverables

## Objectives
1. Eliminate production-unsafe feed generation (remove `FakeEmbedder()` instantiation and broad exception suppression).
2. Restore catalog hydration and feed candidate delivery with actionable `empty_reason` diagnostics.
3. Validate wardrobe persistence (saving items, listing items, removing items, cross-user isolation).
4. Verify backend authentication, consent, and user preference endpoints.
5. Capture an authoritative OpenAPI snapshot in `audit/reports/rc01/openapi.json`.
6. Establish reliable mobile-to-backend API connectivity requirements for physical and emulator environments.

## Scope Boundaries
- **Backend-focused recovery**: Fix backend defects preventing end-to-end data flow.
- **Contract alignment**: Identify and document discrepancies between mobile client payloads and FastAPI backend schemas (e.g., category enum names vs occasion tags, rupee amounts vs minor units).
- **Zero test regressions**: Maintain passing status across existing unit and security test suites under `-m "not frozen"`.

## Non-Goals (Out of Scope for RC-01)
- **No Mobile UI Redesign**: Redesigning screens, layouts, and component aesthetics is reserved for Development Cycle RC-02.
- **No Commerce Boundary Reopening**: ADR-0001 frozen commerce routes (`/api/v1/checkout`, `/api/v1/orders`, etc.) remain frozen.
- **No Production AI Provider Replacement**: The mock try-on provider and local enrichment providers remain default for local development. Full third-party AI provider integration is reserved for later cycles.
- **No Evidence or Governance Modifications**: No modifications to `docs/evidence/`, `docs/provenance.md`, or `docs/release/gates.md` (reserved strictly for human founder).
- **No Direct Commits to `main`**: All work is staged and pushed on branch `recovery/rc01-backend`.

## Deliverables Register
| Deliverable ID | Description | Location |
| :--- | :--- | :--- |
| D01.01 | Production feed generation fix (no FakeEmbedder) | `backend/fashx/recommendation/application/generate_feed.py` |
| D01.02 | Actionable empty-feed diagnostic schema | `backend/fashx/recommendation/application/generate_feed.py` |
| D01.03 | Cold-start and empty-feed unit test coverage | `tests/unit/test_recommendation_use_case.py` |
| D01.04 | Catalog source registration and seed hydration | `fashx_local.db` (20 items seeded) |
| D01.05 | Wardrobe CRUD verification | `tests/unit/test_mvp5_closet_shopping_journey.py` & live API verification |
| D01.06 | Authoritative OpenAPI snapshot | `audit/reports/rc01/openapi.json` |
| D01.07 | RC-01 documentation package | `docs/reengineering/RC01/` |
