import copy
import re
from typing import Any

from contracts.src.loader import load_manifest
from jsonschema import Draft202012Validator, ValidationError

MALICIOUS_PAYLOAD_REGEX = re.compile(
    r"<script|javascript:|onerror=|onload=|eval\(|vbscript:|data:text/html",
    re.IGNORECASE,
)


class ComponentNotFoundError(Exception):
    def __init__(self, component_id: str):
        super().__init__(f"Component '{component_id}' is not registered in the platform catalogue")
        self.component_id = component_id


class InvalidSlotPlacementError(Exception):
    def __init__(self, component_id: str, slot: str, allowed: list[str]):
        super().__init__(f"Component '{component_id}' cannot be placed in slot '{slot}'. Allowed slots: {allowed}")
        self.component_id = component_id
        self.slot = slot
        self.allowed = allowed


class InvalidComponentPropertyError(Exception):
    def __init__(self, component_id: str, message: str, path: str | None = None):
        super().__init__(f"Invalid properties for '{component_id}': {message}")
        self.component_id = component_id
        self.message = message
        self.path = path


class RetiredComponentError(Exception):
    def __init__(self, component_id: str):
        super().__init__(f"Component '{component_id}' is retired and cannot be newly instantiated")
        self.component_id = component_id


class MaliciousPayloadError(Exception):
    def __init__(self, path: str, payload: str):
        super().__init__(f"Malicious executable script/payload rejected at {path}: {payload}")
        self.path = path
        self.payload = payload


class ComponentRegistry:
    def __init__(self) -> None:
        manifest = load_manifest("component-catalogue.json")
        self._components: dict[str, dict[str, Any]] = {}
        self._validators: dict[str, Draft202012Validator] = {}
        for c in manifest.get("components", []):
            cid = c["id"]
            self._components[cid] = c
            prop_schema = c.get("property_schema", {})
            self._validators[cid] = Draft202012Validator(prop_schema)

    def get_component(self, component_id: str) -> dict[str, Any]:
        if component_id not in self._components:
            raise ComponentNotFoundError(component_id)
        return copy.deepcopy(self._components[component_id])

    def list_components(self) -> list[dict[str, Any]]:
        return [copy.deepcopy(c) for c in self._components.values()]

    def validate_instance(self, instance: dict[str, Any]) -> None:
        component_id = instance.get("component_id")
        if not component_id or component_id not in self._components:
            raise ComponentNotFoundError(component_id or "unknown")

        defn = self._components[component_id]
        if defn.get("status") == "retired":
            raise RetiredComponentError(component_id)

        # Validate slot
        slot = str(instance.get("slot") or "unknown")
        allowed_slots = defn.get("allowed_slots", [])
        if slot not in allowed_slots:
            raise InvalidSlotPlacementError(component_id, slot, allowed_slots)

        # Validate props and check for malicious code
        props = instance.get("props", {})
        self._check_safety(props, f"component[{instance.get('id', component_id)}].props")

        validator = self._validators.get(component_id)
        if validator is None:
            validator = Draft202012Validator(defn.get("property_schema", {}))
            self._validators[component_id] = validator
        try:
            validator.validate(props)
        except ValidationError as e:
            path_str = ".".join(str(p) for p in e.absolute_path)
            raise InvalidComponentPropertyError(component_id, e.message, path_str)

    def _check_safety(self, obj: Any, current_path: str) -> None:
        if isinstance(obj, str):
            if MALICIOUS_PAYLOAD_REGEX.search(obj):
                raise MaliciousPayloadError(current_path, obj)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                self._check_safety(v, f"{current_path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                self._check_safety(v, f"{current_path}[{i}]")


_DEFAULT_COMPONENT_REGISTRY = ComponentRegistry()


def get_component_registry() -> ComponentRegistry:
    return _DEFAULT_COMPONENT_REGISTRY
