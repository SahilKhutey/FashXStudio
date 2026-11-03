# RC-02 — Scope & Deliverables

## Objectives
1. Replace disconnected and empty frontend states with backend-connected consumer experiences.
2. Establish a shared design system with reusable components (`Button`, `ProductCard`, `SearchBar`, `CategoryChip`, `SectionHeader`, `ProductSkeleton`, `Badge`).
3. Re-engineer the primary navigation shell with 4 destinations: Discover (`feed`), Explore (`explore`), Looks (`looks`), and Closet (`closet`), plus Settings access.
4. Repair the missing `explore.tsx` route to eliminate the broken navigation target from the Closet screen (BP-03).
5. Deliver contextual recovery in the Discover Feed distinguishing `"catalog_empty"` from `"all_candidates_filtered"`.
6. Ensure 100% TypeScript type safety (`tsc --noEmit` passing with 0 errors) and complete Jest test suite green status (`19 passed, 137 passed`).

## Scope Boundaries
- **Mobile frontend focused**: Re-architect and refine presentation, components, and screen controllers in `mobile/`.
- **Backend preservation**: Consume the live FastAPI backend contracts validated in RC-01 without modifying backend business logic.
- **Mock provider labeling**: Mock virtual try-on providers must remain explicitly labeled with `"PREVIEW ONLY"` watermarks; no simulated artificial intelligence claims.
- **Zero test regressions**: All existing mobile tests and backend tests must remain passing.

## Non-Goals (Out of Scope for RC-02)
- No modification of files in `docs/evidence/`, `docs/provenance.md`, or `docs/release/gates.md` (reserved strictly for founder per `AGENTS.md`).
- No commercial checkout / payment gateway implementation (ADR-0001 frozen commerce boundaries remain frozen).
- No third-party AI GPU infrastructure deployment (handled in subsequent cycles).
- No direct merge to `main`.
