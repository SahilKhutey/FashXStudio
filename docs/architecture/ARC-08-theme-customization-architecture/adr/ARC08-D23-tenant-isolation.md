# ADR ARC08-D23-tenant-isolation: Composite Tenant Foreign Keys & RLS

## Status
Accepted

## Context & Decision
Tenant isolation is enforced via relational composite keys and RLS policies.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
