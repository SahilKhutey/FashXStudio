# ADR ARC08-D09-responsive-system: Platform-Controlled Breakpoints

## Status
Accepted

## Context & Decision
Breakpoints are strictly fixed at 320px, 375px, 768px, 1024px, and 1440px.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
