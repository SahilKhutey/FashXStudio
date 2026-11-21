# ADR ARC08-D16-editor-architecture: Shared Configuration Contract

## Status
Accepted

## Context & Decision
Settings Editor and Visual Editor operate on the same canonical document.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
