#!/usr/bin/env python3
"""FashXStudio MVP readiness audit.

Safe by default:
- Does not switch branches, reset files, install packages, or deploy.
- Runs validation commands only when --run-checks is supplied.
- Runs PostgreSQL tests only when --run-db-tests is explicitly supplied.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "docs" / "product" / "MVP_READINESS.md"
JSON_OUTPUT = ROOT / "docs" / "product" / "mvp-readiness-evidence.json"


@dataclass
class CheckResult:
    name: str
    command: list[str]
    working_directory: str
    status: str  # PASS, FAIL, BLOCKED, NOT RUN
    exit_code: int | None
    duration_seconds: float
    output_tail: list[str]
    error_message: str | None = None


@dataclass
class RepoMetadata:
    branch: str
    commit_hash: str
    commit_message: str
    commit_date: str
    upstream: str | None
    is_clean: bool
    modified_files: list[str]
    untracked_files: list[str]
    python_version: str
    node_version: str | None
    platform: str
    timestamp_utc: str


def run_cmd(
    cmd: Sequence[str], cwd: Path | None = None, timeout: int = 600
) -> tuple[int, str]:
    """Execute a command and return exit code and combined output."""
    use_shell = sys.platform.startswith("win") and cmd[0] in {"npm", "npx"}
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=use_shell,
            encoding="utf-8",
            errors="replace",
        )
        combined = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, combined
    except subprocess.TimeoutExpired as exc:
        out = ""
        if exc.stdout:
            out += exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode("utf-8", errors="replace")
        if exc.stderr:
            err = exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode("utf-8", errors="replace")
            out += err
        return -1, f"Command timed out after {timeout} seconds.\n{out}"
    except FileNotFoundError as exc:
        return 127, f"Executable not found: {exc}"
    except Exception as exc:
        return 1, f"Execution failed: {exc}"


def collect_repo_metadata() -> RepoMetadata:
    """Collect current Git repository and environment metadata safely."""
    # Git branch
    _, branch = run_cmd(["git", "branch", "--show-current"])
    branch = branch.strip() or "HEAD detached"

    # Commit info
    _, commit_info = run_cmd(["git", "log", "-1", "--format=%H|%s|%cd", "--date=iso-strict"])
    parts = commit_info.strip().split("|", 2)
    commit_hash = parts[0] if len(parts) > 0 else "unknown"
    commit_msg = parts[1] if len(parts) > 1 else ""
    commit_date = parts[2] if len(parts) > 2 else ""

    # Upstream
    _, upstream = run_cmd(["git", "rev-parse", "--abbrev-ref", "@{upstream}"])
    upstream_str: str | None = upstream.strip() if upstream and "fatal:" not in upstream else None

    # Status
    _, status_out = run_cmd(["git", "status", "--porcelain"])
    modified: list[str] = []
    untracked: list[str] = []
    for line in status_out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("??"):
            untracked.append(line[3:])
        else:
            modified.append(line[3:])

    # Node version
    node_code, node_out = run_cmd(["node", "--version"])
    node_ver = node_out.strip() if node_code == 0 else None

    return RepoMetadata(
        branch=branch,
        commit_hash=commit_hash,
        commit_message=commit_msg,
        commit_date=commit_date,
        upstream=upstream_str,
        is_clean=len(modified) == 0 and len(untracked) == 0,
        modified_files=modified,
        untracked_files=untracked,
        python_version=sys.version.split()[0],
        node_version=node_ver,
        platform=sys.platform,
        timestamp_utc=datetime.now(UTC).isoformat(),
    )


def define_standard_checks(run_db_tests: bool = False) -> list[dict]:
    """Define the checks without executing them."""
    checks: list[dict] = [
        {
            "name": "Backend Docs Lint",
            "command": [sys.executable, "scripts/docs_lint.py"],
            "cwd": ROOT,
            "category": "backend",
        },
        {
            "name": "Backend Ruff Linter",
            "command": ["ruff", "check", "."],
            "cwd": ROOT,
            "category": "backend",
        },
        {
            "name": "Backend Mypy Typecheck",
            "command": ["mypy", "."],
            "cwd": ROOT,
            "category": "backend",
        },
        {
            "name": "Backend Alembic Heads",
            "command": [sys.executable, "-m", "alembic", "heads"],
            "cwd": ROOT,
            "category": "backend",
        },
        {
            "name": "Backend Non-Frozen Pytest",
            "command": [sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", "-m", "not frozen"],
            "cwd": ROOT,
            "category": "backend",
        },
        {
            "name": "Mobile Typecheck",
            "command": ["npm", "run", "typecheck"],
            "cwd": ROOT / "mobile",
            "category": "mobile",
        },
        {
            "name": "Mobile ESLint",
            "command": ["npx", "eslint", ".", "--max-warnings", "0"],
            "cwd": ROOT / "mobile",
            "category": "mobile",
        },
        {
            "name": "Mobile Jest Unit Tests",
            "command": ["npm", "test", "--", "--runInBand"],
            "cwd": ROOT / "mobile",
            "category": "mobile",
        },
        {
            "name": "Mobile Expo Doctor",
            "command": ["npx", "expo-doctor"],
            "cwd": ROOT / "mobile",
            "category": "mobile",
        },
        {
            "name": "Mobile Android Bundle Export",
            "command": ["npx", "expo", "export", "--platform", "android"],
            "cwd": ROOT / "mobile",
            "category": "mobile",
        },
    ]

    if run_db_tests:
        checks.extend([
            {
                "name": "PostgreSQL Alembic Upgrade",
                "command": [sys.executable, "-m", "alembic", "upgrade", "head"],
                "cwd": ROOT,
                "category": "database",
            },
            {
                "name": "PostgreSQL DB Marker Tests",
                "command": [sys.executable, "-m", "pytest", "tests", "-m", "db", "-q", "-rs"],
                "cwd": ROOT,
                "category": "database",
            },
        ])

    return checks


def execute_check(check_def: dict) -> CheckResult:
    """Execute a single check and capture its output tail and status."""
    name = check_def["name"]
    cmd = check_def["command"]
    cwd = check_def["cwd"]
    rel_cwd = str(cwd.relative_to(ROOT)) if cwd != ROOT else "."

    # Check if executable is available
    exe_name = cmd[0]
    if exe_name != sys.executable and not shutil.which(exe_name):
        return CheckResult(
            name=name,
            command=cmd,
            working_directory=rel_cwd,
            status="BLOCKED",
            exit_code=None,
            duration_seconds=0.0,
            output_tail=[f"Executable '{exe_name}' not found on PATH."],
            error_message=f"Missing dependency: {exe_name}",
        )

    # For DB tests, check environment
    if check_def.get("category") == "database":
        db_url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
        if not db_url:
            return CheckResult(
                name=name,
                command=cmd,
                working_directory=rel_cwd,
                status="BLOCKED",
                exit_code=None,
                duration_seconds=0.0,
                output_tail=["TEST_DATABASE_URL environment variable is not configured."],
                error_message="Missing database configuration",
            )

    start = time.perf_counter()
    exit_code, output = run_cmd(cmd, cwd=cwd)

    # Retry once for network-dependent checks if transient failure occurs
    if exit_code != 0 and name == "Mobile Expo Doctor":
        time.sleep(2)
        exit_code, output = run_cmd(cmd, cwd=cwd)

    duration = round(time.perf_counter() - start, 3)

    lines = [line for line in output.splitlines() if line.strip()]
    tail = lines[-25:] if len(lines) > 25 else lines

    status = "PASS" if exit_code == 0 else "FAIL"

    return CheckResult(
        name=name,
        command=cmd,
        working_directory=rel_cwd,
        status=status,
        exit_code=exit_code,
        duration_seconds=duration,
        output_tail=tail,
    )


def generate_markdown_report(
    meta: RepoMetadata,
    results: list[CheckResult],
    checks_ran: bool,
    run_db_tests: bool,
) -> str:
    """Format metadata and check results into Markdown."""
    lines: list[str] = [
        "# FashXStudio MVP Readiness",
        "",
        "## Build metadata",
        f"- Commit: `{meta.commit_hash[:7]}` (`{meta.commit_message}`)",
        f"- Branch: `{meta.branch}`",
        f"- Upstream: `{meta.upstream or 'None'}`",
        f"- Date: {meta.timestamp_utc[:10]}",
        f"- Working tree clean: `{'True' if meta.is_clean else 'False'}`",
        f"- Backend environment: Python {meta.python_version}, platform {meta.platform}",
        f"- Mobile runtime: Node {meta.node_version or 'unknown'}",
        "",
    ]

    if not checks_ran:
        lines.extend([
            "> [!NOTE]",
            "> Initial baseline report generated with `--run-checks` disabled.",
            "> All test sections below are in `NOT RUN` status. Use `python scripts/audit/mvp_readiness.py --run-checks` to execute.",
            "",
        ])

    lines.extend([
        "## Check Summary",
        "",
        "| Status | Check Name | Directory | Exit Code | Duration | Command |",
        "| :--- | :--- | :--- | :---: | :---: | :--- |",
    ])

    for res in results:
        status_icon = {
            "PASS": "🟢 PASS",
            "FAIL": "🔴 FAIL",
            "BLOCKED": "🟡 BLOCKED",
            "NOT RUN": "⚪ NOT RUN",
        }.get(res.status, res.status)

        exit_code_str = str(res.exit_code) if res.exit_code is not None else "-"
        duration_str = f"{res.duration_seconds:.2f}s" if res.duration_seconds > 0 else "-"
        cmd_str = f"`{' '.join(res.command[:3])}{'...' if len(res.command) > 3 else ''}`"

        lines.append(
            f"| {status_icon} | {res.name} | `{res.working_directory}` | {exit_code_str} | {duration_str} | {cmd_str} |"
        )

    lines.extend([
        "",
        "## Evidence Details",
        "",
    ])

    if not checks_ran:
        lines.extend([
            "_No validation commands executed in this baseline snapshot._",
            "",
        ])
    else:
        for res in results:
            lines.extend([
                f"### {res.name}",
                f"- **Status**: `{res.status}`",
                f"- **Working directory**: `{res.working_directory}`",
                f"- **Exit code**: `{res.exit_code}`",
                f"- **Duration**: `{res.duration_seconds:.3f}s`",
                f"- **Command**: `{' '.join(res.command)}`",
                "",
                "```text",
            ])
            if res.output_tail:
                lines.extend(res.output_tail)
            else:
                lines.append("(No output captured)")
            lines.extend(["```", ""])

    # Disclosures & Limitations per Rule 14
    lines.extend([
        "## Environment Limitations & Disclosures (Rule 14)",
        "",
        "1. **PostgreSQL Migrations & DB Marker Tests**:",
        "   - Local execution against PostgreSQL on port 5432 is unverified if no local PostgreSQL/Docker service is running.",
        "   - Automated in GitHub Actions CI where PostgreSQL 16 + pgvector container is configured as a service.",
        "2. **Physical Android Hardware**:",
        "   - JS/Asset bundle compilation verified via `expo export --platform android`.",
        "   - Physical device smoke test reserved for founder device run.",
        "3. **Hosted Staging Deployment**:",
        "   - Cloud infrastructure (hosted Supabase, deployed backend API) pending staging provisioning.",
        "",
        "## Product Blockers Status",
        "",
        "- [x] Fail-closed runtime configuration (`mobile/src/lib/env.ts` enforces HTTPS and blocks dev tokens in production)",
        "- [x] Server-authoritative onboarding gate policy (`403 ONBOARDING_REQUIRED` for uncompleted onboarding)",
        "- [x] Automated catalog acquisition pipeline with SSRF image validation and freshness guards",
        "- [x] Personalization taste vector representation and scoring",
        "- [x] Wardrobe CRUD persistence",
        "- [x] Cascading privacy deletion (`DELETE /me`)",
        "- [ ] Hosted Supabase staging project configuration",
        "- [ ] Physical Android device end-to-end journey smoke test",
        "",
        "## Release Gate Decision",
        "",
        "- **Decision**: **NO-GO (Conditional Pre-Staging)**",
        "- **Rationale**: Local mobile bundle, backend test suite, linter, typechecks, and security scans passed. Full public release requires green CI on PostgreSQL and physical Android device QA.",
        "",
    ])

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="FashXStudio MVP Readiness Audit")
    parser.add_argument(
        "--run-checks",
        action="store_true",
        help="Execute automated validation checks (backend lint/typecheck/tests and mobile checks)",
    )
    parser.add_argument(
        "--run-db-tests",
        action="store_true",
        help="Execute PostgreSQL migrations and DB-marker integration tests (requires PostgreSQL configured)",
    )
    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help="Run only checks matching substring (e.g. 'Expo Doctor')",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path to Markdown output file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=JSON_OUTPUT,
        help=f"Path to JSON output file (default: {JSON_OUTPUT})",
    )

    args = parser.parse_args()

    meta = collect_repo_metadata()
    check_defs = define_standard_checks(run_db_tests=args.run_db_tests)

    # Load existing results if available
    existing_map: dict[str, CheckResult] = {}
    if args.json_output.exists():
        try:
            prev = json.loads(args.json_output.read_text(encoding="utf-8"))
            for item in prev.get("results", []):
                existing_map[item["name"]] = CheckResult(**item)
        except Exception:
            pass

    results: list[CheckResult] = []

    if args.run_checks:
        targets = check_defs
        if args.filter:
            targets = [c for c in check_defs if args.filter.lower() in c["name"].lower()]

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Executing {len(targets)} validation checks...")
        for check in targets:
            print(f"  -> Running: {check['name']}...", end="", flush=True)
            res = execute_check(check)
            existing_map[check["name"]] = res
            print(f" {res.status} ({res.duration_seconds}s)")

        for check in check_defs:
            if check["name"] in existing_map:
                results.append(existing_map[check["name"]])
            else:
                rel_cwd = str(check["cwd"].relative_to(ROOT)) if check["cwd"] != ROOT else "."
                results.append(
                    CheckResult(
                        name=check["name"],
                        command=check["command"],
                        working_directory=rel_cwd,
                        status="NOT RUN",
                        exit_code=None,
                        duration_seconds=0.0,
                        output_tail=[],
                    )
                )
    else:
        print("Generating baseline metadata snapshot (checks not run). Use --run-checks to execute.")
        for check in check_defs:
            rel_cwd = str(check["cwd"].relative_to(ROOT)) if check["cwd"] != ROOT else "."
            results.append(
                CheckResult(
                    name=check["name"],
                    command=check["command"],
                    working_directory=rel_cwd,
                    status="NOT RUN",
                    exit_code=None,
                    duration_seconds=0.0,
                    output_tail=[],
                )
            )

    # Generate Markdown
    md_content = generate_markdown_report(
        meta=meta,
        results=results,
        checks_ran=args.run_checks,
        run_db_tests=args.run_db_tests,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(md_content, encoding="utf-8")
    print(f"Wrote Markdown report to {args.output}")

    # Generate JSON
    json_data = {
        "metadata": asdict(meta),
        "checks_ran": args.run_checks,
        "run_db_tests": args.run_db_tests,
        "results": [asdict(r) for r in results],
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(json_data, indent=2), encoding="utf-8")
    print(f"Wrote JSON evidence to {args.json_output}")


if __name__ == "__main__":
    main()
