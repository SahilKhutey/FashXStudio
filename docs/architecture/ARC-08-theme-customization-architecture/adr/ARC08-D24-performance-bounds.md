# ADR ARC08-D24-performance-bounds: Configuration Payload & Depth Limits

## Status
Accepted

## Context & Decision
Payloads are capped at 512 KB, 8 nesting levels, and 100 component instances.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
