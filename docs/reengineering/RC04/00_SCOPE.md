# RC-04 — Scope & Deliverables

## Objectives
1. **Resolve FX-009**: Replace developer diagnostics and raw internal database UUIDs on the Settings screen with a modern, consumer-grade profile and account control interface.
2. **Resolve FX-005**: Automate local area network (LAN) IP resolution for physical device evaluation via Expo Go QR code.
3. **Preserve DPDP Compliance**: Guarantee that photo deletion, consent revocation, and irreversible account erasure remain strictly functional and test-verified.
4. **Maintain Full Test Health**: 100% green status across Jest unit tests, TypeScript type checks, and backend integration test suites.

## Scope Boundaries
- **Mobile Presentation Polish**: Focuses on `mobile/app/settings/index.tsx` and design system integration.
- **Developer Tooling**: Tooling in `scripts/mobile/configure_lan_api.py`.
- **Zero Backend Business Logic Changes**: Backend routes remain unchanged.

## Non-Goals (Out of Scope for RC-04)
- No modification of files in `docs/evidence/`, `docs/provenance.md`, or `docs/release/gates.md`.
- No payment gateway / direct checkout integration (frozen per ADR-0001).
- No direct commit to `main`.
