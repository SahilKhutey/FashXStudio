# ADR ARC08-D01-customization-model: Configuration-Driven Customization

## Status
Accepted

## Context & Decision
Restaurant customizations are declarative JSON configuration documents, completely decoupled from application code.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
