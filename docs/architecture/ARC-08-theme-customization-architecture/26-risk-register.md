# ARC-08: 26 — Risk Register

## 1. Architectural Risks and Mitigations
| Risk | Severity | Mitigation |
| :--- | :--- | :--- |
| **Arbitrary CSS / Script Injection** | Critical | Strict token allowlists, regex validation, rejection of CSS expressions |
| **Cross-Tenant Configuration Leak** | Critical | Relational composite keys, PostgreSQL RLS, trusted context scoping |
| **Theme Updates Breaking Published Menus** | Critical | Immutable snapshots with exact version pinning in ARC-10 |
| **Divergence Between Settings and Visual Editors** | High | Single shared canonical JSON Schema configuration document |
| **Concurrent Edit Overwrite** | High | Optimistic concurrency control via `If-Match` revision ETags |
| **Excessive Configuration Size** | Medium | Bounded payload limits (512 KB) and component counts (max 100) |
