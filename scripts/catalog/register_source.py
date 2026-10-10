"""CLI tool to register a catalog source in pending status.

Usage:
    python scripts/catalog/register_source.py --slug brand-a --name "Brand A" --kind feed_url --image-policy mirror
"""

import argparse
import asyncio
import sys

from sqlalchemy import select

from database.models.catalog import CatalogSource
from fashx.core.database import get_session_factory


async def register_source(args: argparse.Namespace) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Check if slug exists
        stmt = select(CatalogSource).where(CatalogSource.slug == args.slug)
        existing = (await session.scalars(stmt)).first()
        if existing is not None:
            print(f"Error: Source with slug '{args.slug}' already exists (status: {existing.status}).", file=sys.stderr)
            sys.exit(1)

        source = CatalogSource(
            slug=args.slug,
            name=args.name,
            kind=args.kind,
            status="pending",
            rights_display=False,
            rights_tryon=False,
            image_policy=args.image_policy,
            refresh_hours=args.refresh_hours,
            max_rps=args.max_rps,
            terms_url=args.terms_url,
            takedown_contact=args.takedown_contact,
            notes=args.notes,
        )
        session.add(source)
        await session.commit()
        print(f"Successfully registered source '{args.slug}' ({args.name}) [status: pending, policy: {args.image_policy}].")
        print("Note: Source is pending and excluded from feeds. Use clear_source.py with evidence to clear.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Register a catalog source in pending status.")
    parser.add_argument("--slug", required=True, help="Unique source identifier (e.g., fabindia, westside)")
    parser.add_argument("--name", required=True, help="Human-readable brand/partner name")
    parser.add_argument("--kind", choices=["api", "feed_url", "file_drop", "manual"], default="feed_url", help="Source ingestion type")
    parser.add_argument("--image-policy", choices=["hotlink", "mirror"], default="mirror", help="Image handling policy")
    parser.add_argument("--refresh-hours", type=int, default=24, help="Refresh frequency in hours")
    parser.add_argument("--max-rps", type=float, default=2.0, help="Max requests per second rate limit")
    parser.add_argument("--terms-url", default=None, help="URL to terms of use / agreement")
    parser.add_argument("--takedown-contact", default=None, help="Email/contact for takedown requests")
    parser.add_argument("--notes", default=None, help="Initial internal notes")

    args = parser.parse_args()
    asyncio.run(register_source(args))


if __name__ == "__main__":
    main()
