from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def audit_github(root: Path) -> dict[str, Any]:
    inside_repo = bool(git(root, "rev-parse", "--show-toplevel"))
    if not inside_repo:
        return {
            "status": "not_a_git_repository",
        }

    status_output = git(root, "status", "--porcelain")
    remotes = git(root, "remote", "-v")
    recent_commits = git(root, "log", "-n", "5", "--oneline")

    return {
        "status": "success",
        "root": git(root, "rev-parse", "--show-toplevel"),
        "branch": git(root, "branch", "--show-current"),
        "head": git(root, "rev-parse", "HEAD"),
        "clean_working_tree": len(status_output) == 0,
        "recent_commits": recent_commits.splitlines() if recent_commits else [],
        "remotes": remotes.splitlines() if remotes else [],
    }
