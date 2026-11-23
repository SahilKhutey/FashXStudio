# ADR ARC08-D15-revision-management: Immutable Revision Records

## Status
Accepted

## Context & Decision
Every saved configuration creates an immutable revision record in customization_revisions.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
