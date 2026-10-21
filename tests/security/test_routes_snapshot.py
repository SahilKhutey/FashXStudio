from __future__ import annotations

from pathlib import Path

from fashx.core.settings import Settings
from fashx.main import app as global_app
from fashx.main import create_app


def test_openapi_routes_match_snapshot() -> None:
    snapshot_path = Path(__file__).parent / "routes.snapshot.txt"
    assert snapshot_path.exists(), "routes.snapshot.txt must exist"

    expected_routes = [
        line.strip()
        for line in snapshot_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

    import os
    orig_frozen = os.environ.pop("FASHX_ENABLE_FROZEN", None)
    try:
        settings = Settings(enable_b2b=False, enable_frozen=False)
        app = create_app(settings)
        paths = app.openapi()["paths"]
    finally:
        if orig_frozen is not None:
            os.environ["FASHX_ENABLE_FROZEN"] = orig_frozen

    actual_routes = []
    for p, path_item in paths.items():
        for m in path_item.keys():
            if m.upper() not in ("OPTIONS", "HEAD"):
                actual_routes.append(f"{m.upper()} {p}")

    actual_routes.sort()
    expected_routes.sort()

    diff_added = set(actual_routes) - set(expected_routes)
    diff_removed = set(expected_routes) - set(actual_routes)

    assert not diff_added and not diff_removed, (
        f"OpenAPI route surface changed!\n"
        f"Added ({len(diff_added)}): {sorted(diff_added)}\n"
        f"Removed ({len(diff_removed)}): {sorted(diff_removed)}\n"
        f"If intentional, update tests/security/routes.snapshot.txt."
    )
    assert len(actual_routes) == len(expected_routes)


def test_global_app_routes_match_snapshot_no_leak() -> None:
    snapshot_path = Path(__file__).parent / "routes.snapshot.txt"
    assert snapshot_path.exists(), "routes.snapshot.txt must exist"

    expected_routes = [
        line.strip()
        for line in snapshot_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

    paths = global_app.openapi()["paths"]
    actual_routes = []
    for p, path_item in paths.items():
        for m in path_item.keys():
            if m.upper() not in ("OPTIONS", "HEAD"):
                actual_routes.append(f"{m.upper()} {p}")

    actual_routes.sort()
    expected_routes.sort()

    diff_added = set(actual_routes) - set(expected_routes)
    diff_removed = set(expected_routes) - set(actual_routes)

    assert not diff_added and not diff_removed, (
        f"Global app route leak detected!\n"
        f"Added routes ({len(diff_added)}): {sorted(diff_added)}\n"
        f"Removed routes ({len(diff_removed)}): {sorted(diff_removed)}\n"
        f"Ensure test fixtures and route tests always use create_app(), never mutating global fashx.main.app."
    )
