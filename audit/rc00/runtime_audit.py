from __future__ import annotations

from pathlib import Path
from typing import Any

SENSITIVE_KEYS = {
    "AUTH_JWT_SECRET",
    "FASHN_API_KEY",
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "DATABASE_URL",
    "REDIS_URL",
}


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def audit_runtime(root: Path) -> dict[str, Any]:
    env_example = root / ".env.example"
    values = parse_env_file(env_example)

    mock_tryon = values.get("TRYON_PROVIDER") == "mock"
    local_auth = values.get("AUTH_MODE") == "local"
    memory_repo = values.get("REPO_BACKEND") == "memory"
    local_storage = values.get("STORAGE_BACKEND") == "local"

    # Redact sensitive keys
    sanitized: dict[str, str] = {}
    secret_values_exposed = False
    for k, v in values.items():
        if k in SENSITIVE_KEYS:
            if v and v != "":
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = "[EMPTY]"
        else:
            sanitized[k] = v

    findings: list[dict[str, Any]] = []
    if mock_tryon:
        findings.append({
            "id": "RC00-R001",
            "severity": "P0",
            "subsystem": "runtime",
            "status": "CONFIRMED",
            "title": "Mock try-on is the documented default",
            "evidence": ".env.example",
            "recommendation": "Verify actual runtime provider and test real inference.",
        })
    if local_auth:
        findings.append({
            "id": "RC00-R002",
            "severity": "P1",
            "subsystem": "runtime",
            "status": "CONFIRMED",
            "title": "Local authentication is the documented default",
            "evidence": ".env.example",
            "recommendation": "Verify authentication mode in the running environment.",
        })

    return {
        "status": "success",
        "env_example_exists": env_example.is_file(),
        "sanitized_defaults": sanitized,
        "secret_values_exposed": secret_values_exposed,
        "risk_checks": {
            "mock_tryon_default": mock_tryon,
            "local_auth_default": local_auth,
            "memory_repo_default": memory_repo,
            "local_storage_default": local_storage,
        },
        "findings": findings,
    }
