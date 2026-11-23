# ARC-08: 02 — Design Principles & Invariants

## 1. Mandatory Architectural Invariants
- **Rule I01 (No Arbitrary Code)**: Restaurant customizations must never execute user-supplied JavaScript, unsafe CSS expressions, or inline event handlers.
- **Rule I02 (Strict Schema Enforcement)**: Any configuration document failing JSON Schema Draft 2020-12 validation is rejected server-side with structured errors.
- **Rule I03 (Immutable Published Snapshots)**: Once published via ARC-10, menu customizations are pinned to exact immutable versions and never mutate retrospectively.
- **Rule I04 (Complete Tenant Isolation)**: Tenant ownership resides in relational columns (`organization_id`, `menu_id`) guarded by PostgreSQL RLS. Customization JSONB cannot define tenant boundaries.
- **Rule I05 (Deterministic Resolution)**: Given identical inputs, theme resolution must produce byte-for-byte identical output without side effects.
- **Rule I06 (Pure Package Independence)**: Core customization contracts, tokens, and resolvers must remain pure TypeScript/Python libraries without dependencies on database ORMs or Next.js page lifecycles.
