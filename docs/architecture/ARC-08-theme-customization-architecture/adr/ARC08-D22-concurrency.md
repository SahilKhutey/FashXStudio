# ADR ARC08-D22-concurrency: Optimistic Concurrency Control

## Status
Accepted

## Context & Decision
Concurrent updates are controlled via If-Match revision headers and 409 Conflict responses.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
