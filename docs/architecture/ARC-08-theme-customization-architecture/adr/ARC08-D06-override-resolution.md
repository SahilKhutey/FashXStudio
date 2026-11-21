# ADR ARC08-D06-override-resolution: Deterministic 8-Tier Resolution

## Status
Accepted

## Context & Decision
Overrides are resolved through an explicit 8-tier hierarchy with strict determinism.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
