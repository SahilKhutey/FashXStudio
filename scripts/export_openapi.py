#!/usr/bin/env python3
"""Export OpenAPI spec from FastAPI application."""

from __future__ import annotations

import json
from pathlib import Path

from fashx.main import app


def export_openapi(path: Path | None = None) -> Path:
    if path is None:
        path = Path("openapi.json")
    spec = app.openapi()
    path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    out = export_openapi()
    print(f"Exported OpenAPI spec to {out}")
