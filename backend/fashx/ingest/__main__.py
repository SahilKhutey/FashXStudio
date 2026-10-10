"""CLI entrypoint for running catalog ingestion runs.

Usage:
    python -m fashx.ingest run --source brand-a [--limit 200] [--dry-run] [--feed path/to/feed.csv]
"""

import argparse
import asyncio
import pathlib
import sys

from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage

from .pipeline import IngestPipeline


async def run_cli(args: argparse.Namespace) -> None:
    session_factory = get_session_factory()

    storage = None
    try:
        storage = get_storage()
    except Exception as e:
        print(f"Warning: Storage initialized with error: {e}", file=sys.stderr)

    feed_data = None
    feed_format = args.format or "csv"
    if args.feed:
        feed_path = pathlib.Path(args.feed)
        if not feed_path.exists():
            print(f"Error: Feed file '{args.feed}' does not exist.", file=sys.stderr)
            sys.exit(1)
        feed_data = feed_path.read_bytes()
        if feed_path.suffix.lower() == ".xml":
            feed_format = "xml"

    async with session_factory() as session:
        pipeline = IngestPipeline(session, storage=storage)
        try:
            print(f"Starting ingestion run for source '{args.source}' (dry_run={args.dry_run}, limit={args.limit})...")
            run = await pipeline.run(
                source_slug=args.source,
                feed_data=feed_data,
                feed_format=feed_format,
                limit=args.limit,
                dry_run=args.dry_run,
            )
            print(f"\nIngestion Run Completed: {run.status.upper()}")
            print(f"  Run ID: {run.id}")
            print(f"  Started At: {run.started_at}")
            print(f"  Finished At: {run.finished_at}")
            print("  Counts:")
            for k, v in run.counts.items():
                print(f"    - {k}: {v}")
            if run.error:
                print(f"  Error: {run.error}")
        except Exception as e:
            print(f"Error during ingestion run: {e}", file=sys.stderr)
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="FashX Catalog Ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Execute an ingestion run for a source")
    run_parser.add_argument("--source", required=True, help="Slug of the catalog source")
    run_parser.add_argument("--feed", default=None, help="Path to local feed file (CSV or XML)")
    run_parser.add_argument("--format", choices=["csv", "xml"], default="csv", help="Feed format")
    run_parser.add_argument("--limit", type=int, default=None, help="Limit number of processed records")
    run_parser.add_argument("--dry-run", action="store_true", help="Simulate run without writing database changes")

    args = parser.parse_args()
    if args.command == "run":
        asyncio.run(run_cli(args))


if __name__ == "__main__":
    main()
