import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, RefResolver

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
MANIFESTS_DIR = Path(__file__).resolve().parent.parent / "manifests"


def load_schema(schema_name: str) -> dict[str, Any]:
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema {schema_name} not found at {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_manifest(manifest_name: str) -> dict[str, Any]:
    manifest_path = MANIFESTS_DIR / manifest_name
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest {manifest_name} not found at {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_menu_customization_validator() -> Draft202012Validator:
    schema = load_schema("menu-customization.schema.json")
    instance_schema = load_schema("component-instance.schema.json")
    tokens_schema = load_schema("design-tokens.schema.json")

    # Local schema store to resolve local references without network access
    schema_store = {
        "menu-customization.schema.json": schema,
        "component-instance.schema.json": instance_schema,
        "design-tokens.schema.json": tokens_schema,
        schema.get("$id", ""): schema,
        instance_schema.get("$id", ""): instance_schema,
        tokens_schema.get("$id", ""): tokens_schema,
    }

    resolver = RefResolver(base_uri=schema.get("$id", ""), referrer=schema, store=schema_store)
    return Draft202012Validator(schema, resolver=resolver)
