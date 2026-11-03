from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_DEPENDENCIES = [
    "expo",
    "expo-router",
    "react",
    "react-native",
    "@tanstack/react-query",
    "zustand",
    "zod",
]


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def audit_mobile(root: Path) -> dict[str, Any]:
    mobile = root / "mobile"
    package_path = mobile / "package.json"
    app_path = mobile / "app.json"

    package_exists = package_path.is_file()
    package = read_json(package_path) if package_exists else {}
    app = read_json(app_path) if app_path.is_file() else {}

    dependencies = {
        **package.get("dependencies", {}),
        **package.get("devDependencies", {}),
    }

    missing = [name for name in REQUIRED_DEPENDENCIES if name not in dependencies]

    findings: list[dict[str, Any]] = []
    if not package_exists:
        findings.append({
            "id": "MOBILE-PKG-MISSING",
            "severity": "P0",
            "subsystem": "mobile",
            "status": "CONFIRMED",
            "title": "mobile/package.json does not exist",
            "evidence": "mobile/package.json",
            "recommendation": "Ensure the mobile directory is correctly populated.",
        })
    elif missing:
        findings.append({
            "id": "MOBILE-DEPS-MISSING",
            "severity": "P1",
            "subsystem": "mobile",
            "status": "CONFIRMED",
            "title": f"Mobile missing dependencies: {', '.join(missing)}",
            "evidence": "mobile/package.json",
            "recommendation": f"Add missing dependencies: {', '.join(missing)}",
        })

    # Count screens in app/
    screens = []
    app_dir = mobile / "app"
    if app_dir.is_dir():
        for file in app_dir.rglob("*.tsx"):
            if not file.name.startswith("_"):
                screens.append(str(file.relative_to(mobile)).replace("\\", "/"))

    return {
        "status": "success" if not missing and package_exists else "warning",
        "package_exists": package_exists,
        "app_json_exists": app_path.is_file(),
        "missing_dependencies": missing,
        "dependencies": dependencies,
        "screen_count": len(screens),
        "screens": sorted(screens),
        "expo_sdk_version": dependencies.get("expo", "unknown"),
        "react_native_version": dependencies.get("react-native", "unknown"),
        "findings": findings,
    }
