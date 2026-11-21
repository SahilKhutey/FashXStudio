import copy
from typing import Any


class HistoryManager:
    def __init__(self, max_depth: int = 50) -> None:
        self.max_depth = max_depth
        self._undo_stack: list[dict[str, Any]] = []
        self._redo_stack: list[dict[str, Any]] = []

    def push(self, state: dict[str, Any]) -> None:
        self._undo_stack.append(copy.deepcopy(state))
        if len(self._undo_stack) > self.max_depth:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self, current_state: dict[str, Any]) -> dict[str, Any] | None:
        if not self._undo_stack:
            return None
        prev = self._undo_stack.pop()
        self._redo_stack.append(copy.deepcopy(current_state))
        return prev

    def redo(self, current_state: dict[str, Any]) -> dict[str, Any] | None:
        if not self._redo_stack:
            return None
        nxt = self._redo_stack.pop()
        self._undo_stack.append(copy.deepcopy(current_state))
        return nxt

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0


class EditorSession:
    def __init__(self, initial_config: dict[str, Any], revision: int = 1) -> None:
        self.draft: dict[str, Any] = copy.deepcopy(initial_config)
        self.server_revision: int = revision
        self.mode: str = "settings"  # 'settings' or 'visual'
        self.viewport: str = "1024px"
        self.selected_component_id: str | None = None
        self.has_unsaved_changes: bool = False
        self.history = HistoryManager(max_depth=50)

    def set_mode(self, mode: str) -> None:
        self.mode = mode

    def set_viewport(self, vp: str) -> None:
        self.viewport = vp

    def select_component(self, comp_id: str | None) -> None:
        self.selected_component_id = comp_id

    def set_primary_color(self, hex_color: str) -> None:
        self.history.push(self.draft)
        theme = self.draft.setdefault("theme", {})
        overrides = theme.setdefault("overrides", {})
        color = overrides.setdefault("color", {})
        brand = color.setdefault("brand", {})
        brand["primary"] = hex_color
        self.has_unsaved_changes = True

    def set_layout(self, layout_id: str) -> None:
        self.history.push(self.draft)
        self.draft.setdefault("layout", {})["id"] = layout_id
        self.has_unsaved_changes = True

    def set_component_visibility(self, instance_id: str, visible: bool) -> None:
        self.history.push(self.draft)
        for c in self.draft.get("components", []):
            if c.get("id") == instance_id:
                c["visible"] = visible
        self.has_unsaved_changes = True

    def reorder_component(self, instance_id: str, new_order: int) -> None:
        self.history.push(self.draft)
        for c in self.draft.get("components", []):
            if c.get("id") == instance_id:
                c["order"] = new_order
        self.has_unsaved_changes = True

    def add_component(self, instance: dict[str, Any]) -> None:
        self.history.push(self.draft)
        self.draft.setdefault("components", []).append(copy.deepcopy(instance))
        self.has_unsaved_changes = True

    def can_undo(self) -> bool:
        return self.history.can_undo()

    def can_redo(self) -> bool:
        return self.history.can_redo()

    def undo(self) -> bool:
        restored = self.history.undo(self.draft)
        if restored is not None:
            self.draft = restored
            self.has_unsaved_changes = True
            return True
        return False

    def redo(self) -> bool:
        restored = self.history.redo(self.draft)
        if restored is not None:
            self.draft = restored
            self.has_unsaved_changes = True
            return True
        return False

    def mark_saved(self, new_revision: int) -> None:
        self.server_revision = new_revision
        self.has_unsaved_changes = False
