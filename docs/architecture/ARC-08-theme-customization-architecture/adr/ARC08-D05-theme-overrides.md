# ADR ARC08-D05-theme-overrides: Restaurant-Scoped Overrides

## Status
Accepted

## Context & Decision
Restaurants can override theme tokens within validated boundaries without modifying global presets.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
