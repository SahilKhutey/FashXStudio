from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fashx.catalog.acquisition.sync_service import CatalogSyncService
from fashx.core.database import get_session_factory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a licensed CSV product feed into FashXStudio."
    )
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--source-id", required=True, type=UUID)
    parser.add_argument("--merchant-id", required=True, type=UUID)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("artifacts/catalog-sync-report.json"),
    )
    return parser.parse_args()


async def run(
    args: argparse.Namespace,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> int:
    if not args.file.is_file():
        print(f"Feed file not found: {args.file}", file=sys.stderr)
        return 2

    if session_factory is None:
        session_factory = get_session_factory()
    service = CatalogSyncService(session_factory)

    try:
        report = await service.import_csv_feed(
            file_path=args.file,
            source_id=args.source_id,
            merchant_id=args.merchant_id,
        )
    except Exception as exc:
        print(f"Top-level import failure: {exc}", file=sys.stderr)
        return 2

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    print(f"Wrote import report to {args.report}")
    print(
        f"Summary: {report.imported} imported, {report.failed} failed, {report.total_rows} total rows"
    )

    if report.failed > 0:
        return 1
    return 0


def main() -> None:
    args = parse_args()
    code = asyncio.run(run(args))
    sys.exit(code)


if __name__ == "__main__":
    main()
