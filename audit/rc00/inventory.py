from __future__ import annotations

import hashlib
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    ".expo",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "dist",
    "build",
    ".local_storage",
    ".mypy_cache",
    ".ruff_cache",
}

EXCLUDED_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.test",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".sql",
    ".md",
}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    file_count = 0
    extension_counts: dict[str, int] = defaultdict(int)
    files_by_extension: dict[str, list[str]] = defaultdict(list)
    total_bytes = 0

    for current_root, dirs, files in os.walk(root):
        # Prune excluded directories in-place so os.walk skips them entirely
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file_name in files:
            if file_name in EXCLUDED_FILES or file_name.startswith(".env."):
                continue

            file_path = Path(current_root) / file_name
            suffix = file_path.suffix.lower()

            if suffix in SOURCE_EXTENSIONS or file_name in {
                "Dockerfile",
                "docker-compose.yml",
                "alembic.ini",
            }:
                file_count += 1
                key = suffix or file_name
                extension_counts[key] += 1
                rel_str = str(file_path.relative_to(root)).replace("\\", "/")
                files_by_extension[key].append(rel_str)
                try:
                    total_bytes += file_path.stat().st_size
                except OSError:
                    pass

    return {
        "status": "success",
        "root": str(root),
        "file_count": file_count,
        "total_bytes": total_bytes,
        "extension_counts": dict(extension_counts),
        "files_by_extension": {k: sorted(v) for k, v in files_by_extension.items()},
    }
