from __future__ import annotations

from pathlib import Path
from typing import Any

EXPECTED_MODULES = [
    "catalog",
    "profile",
    "recommendation",
    "tryon",
    "commerce_wardrobe",
    "discovery",
    "security",
    "core",
    "health",
]


def audit_backend(root: Path) -> dict[str, Any]:
    backend = root / "backend" / "fashx"
    findings: list[dict[str, Any]] = []
    modules: dict[str, Any] = {}

    for module in EXPECTED_MODULES:
        path = backend / module
        exists = path.is_dir()
        modules[module] = {
            "exists": exists,
            "path": str(path.relative_to(root)).replace("\\", "/") if exists else f"backend/fashx/{module}",
        }
        if not exists:
            findings.append({
                "id": f"BACKEND-MODULE-{module.upper()}",
                "severity": "P0",
                "subsystem": "backend",
                "status": "CONFIRMED",
                "title": f"Expected backend module '{module}' is missing",
                "evidence": f"backend/fashx/{module}",
                "recommendation": f"Restore or configure backend module '{module}'",
            })

    entrypoint = backend / "main.py"
    has_entrypoint = entrypoint.is_file()

    return {
        "status": "success" if not findings else "warning",
        "has_entrypoint": has_entrypoint,
        "entrypoint": "backend/fashx/main.py",
        "module_count": len([m for m in modules.values() if m["exists"]]),
        "expected_module_count": len(EXPECTED_MODULES),
        "modules": modules,
        "findings": findings,
    }
