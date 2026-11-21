# ADR ARC08-D19-preview: Draft Preview Isolation

## Status
Accepted

## Context & Decision
Draft previews require tenant authentication and emit no-store cache headers.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
