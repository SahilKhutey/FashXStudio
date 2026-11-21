# ADR ARC08-D17-editor-state: Command Pattern and Bounded History

## Status
Accepted

## Context & Decision
Editor state transitions use the Command pattern with a 50-step undo/redo stack.

## Consequences
- Guarantees system safety, performance, and tenant isolation.
- Prevents customer code injection and layout corruption.
