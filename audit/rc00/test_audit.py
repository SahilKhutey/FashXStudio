from __future__ import annotations

from pathlib import Path
from typing import Any


def audit_tests(root: Path) -> dict[str, Any]:
    locations = [
        root / "tests",
        root / "mobile" / "__tests__",
    ]
    inventory: list[str] = []
    for directory in locations:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            if (
                path.name.startswith("test_")
                or path.name.endswith(".test.ts")
                or path.name.endswith(".test.tsx")
                or path.name.endswith(".spec.ts")
                or path.name.endswith(".spec.tsx")
            ):
                inventory.append(str(path.relative_to(root)).replace("\\", "/"))

    backend_tests = [f for f in inventory if f.startswith("tests/")]
    mobile_tests = [f for f in inventory if f.startswith("mobile/")]

    return {
        "status": "success",
        "test_file_count": len(inventory),
        "backend_test_file_count": len(backend_tests),
        "mobile_test_file_count": len(mobile_tests),
        "test_files": sorted(inventory),
        "execution_status": "not_executed_by_inventory",
        "backend_command": "pytest tests -q",
        "mobile_command": "cd mobile && npm test",
    }
