# ADR ARC08-D07-merge-strategy: Schema-Directed Merge with Reset Semantics

## Status
Accepted

## Context & Decision
Merging is deep and schema-directed; null values reset to base preset values.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
