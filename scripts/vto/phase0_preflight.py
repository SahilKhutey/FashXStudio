"""Read-only VTO Phase 0 preflight.

This utility reports configuration and repository readiness.
It never prints secret values and never calls external services.
"""
from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

REQUIRED_PATHS = (
    "backend/fashx/application/ports/tryon.py",
    "backend/fashx/infrastructure/tryon/fashn_api.py",
    "backend/fashx/tryon/application/process_job.py",
    "backend/fashx/catalog",
    "backend/fashx/core/settings.py",
    "tests/unit/test_tryon_adapters.py",
    "docs/architecture/catalog-sources.md",
    "docs/release/gates.md",
)


def build_report(
    root: Path,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build a safe diagnostic report without exposing secret values."""
    env = os.environ if environ is None else environ

    missing_paths = [
        relative for relative in REQUIRED_PATHS if not (root / relative).exists()
    ]
    repository_paths_ok = len(missing_paths) == 0

    provider = env.get("TRYON_PROVIDER", "mock")
    env_mode = env.get("ENV", env.get("APP_ENV", "dev")).lower()
    is_prod = env_mode in ("prod", "production")

    api_key_val = env.get("FASHN_API_KEY", "")
    has_api_key = bool(api_key_val and api_key_val.strip())

    configuration_issues: list[str] = []

    if provider == "mock":
        configuration_issues.append("Mock provider selected: live inference is inactive.")
        if is_prod:
            configuration_issues.append("Production environment cannot use mock provider.")
    elif provider == "fashn_api":
        if not has_api_key:
            configuration_issues.append("Hosted provider selected but FASHN_API_KEY is missing.")
    elif provider == "fashn_selfhost":
        configuration_issues.append("fashn_selfhost provider is not yet implemented.")
    else:
        configuration_issues.append(f"Unknown try-on provider: {provider}")

    # Build safe report dictionary (secrets strictly excluded)
    report: dict[str, Any] = {
        "repository_paths_ok": repository_paths_ok,
        "missing_paths": missing_paths,
        "provider": provider,
        "env": env_mode,
        "is_prod": is_prod,
        "has_api_key": has_api_key,
        "live_inference_verified": False,  # Deliberately always False in static diagnostic
        "configuration_issues": configuration_issues,
    }

    return report


def main() -> int:
    root = Path(__file__).resolve().parent.parent.parent
    report = build_report(root)

    print("=" * 60)
    print("FASHXSTUDIO VTO PHASE 0 PREFLIGHT REPORT")
    print("=" * 60)
    print(f"Repository paths intact : {report['repository_paths_ok']}")
    if not report["repository_paths_ok"]:
        print(f"Missing paths           : {report['missing_paths']}")
    print(f"Active Provider         : {report['provider']}")
    print(f"Environment             : {report['env']}")
    print(f"API Key Present         : {report['has_api_key']}")
    print(f"Live Inference Verified : {report['live_inference_verified']} (requires human evidence)")

    if report["configuration_issues"]:
        print("\nConfiguration notices / issues:")
        for issue in report["configuration_issues"]:
            print(f" - {issue}")
    else:
        print("\nNo configuration issues found.")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
