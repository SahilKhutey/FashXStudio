# ARC-08: 15 — Editor State and History

## 1. Command Pattern & Bounded History
Editor state transitions are encapsulated in explicit Command objects:
- `SetThemeCommand`, `SetTokenOverrideCommand`, `SetLayoutCommand`, `AddComponentCommand`, `RemoveComponentCommand`, `ReorderComponentCommand`.
- The `HistoryManager` maintains a bounded undo/redo stack (50 levels).
- Switching between Settings Editor and Visual Editor preserves the active undo/redo history and unsaved dirty state.
