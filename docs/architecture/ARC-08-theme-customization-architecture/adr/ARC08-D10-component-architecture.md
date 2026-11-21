# ADR ARC08-D10-component-architecture: Platform-Controlled Component Registry

## Status
Accepted

## Context & Decision
Only registered platform components can be instantiated.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
