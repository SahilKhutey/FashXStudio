# ADR ARC08-D21-migration: Deterministic Migration Registry

## Status
Accepted

## Context & Decision
Configuration upgrades are performed through an automated migration service.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
