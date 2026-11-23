# ARC-08: 06 — Theme Inheritance and Resolution

## 1. Merge Semantics
The theme resolver implements deep dictionary merging with explicit null reset semantics:
- When a tenant specifies a valid property override, it replaces the underlying theme default.
- When an override is explicitly set to `null` or omitted, the base theme preset value is preserved (reset behavior).
- Conflicting property specifications are resolved strictly according to the 8-tier hierarchy.

## 2. Resolver Invariants
- **Purity**: The resolver function does not mutate its input arguments.
- **Determinism**: Resolving the same configuration twice produces the exact same resolved tree.
- **Traceability**: The resolved configuration records exact source version metadata for theme, layout, and components.
