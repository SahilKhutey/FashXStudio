# ADR ARC08-D14-configuration-storage: PostgreSQL JSONB with Relational Ownership

## Status
Accepted

## Context & Decision
Customizations are stored in JSONB columns with relational composite foreign keys.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
