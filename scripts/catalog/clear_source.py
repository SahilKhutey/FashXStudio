"""CLI tool to clear a catalog source with mandatory written evidence.

Usage:
    python scripts/catalog/clear_source.py brand-a --evidence-url "docs/evidence/brand-a.md" --display --tryon
"""

import argparse
import asyncio
import sys
from datetime import date

from sqlalchemy import select

from database.models.catalog import CatalogSource
from fashx.core.database import get_session_factory


async def clear_source(args: argparse.Namespace) -> None:
    if not args.evidence_url or not args.evidence_url.strip():
        print("Error: --evidence-url is required. Refusing to clear source without verifiable evidence.", file=sys.stderr)
        sys.exit(1)

    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(CatalogSource).where(CatalogSource.slug == args.slug)
        source = (await session.scalars(stmt)).first()
        if source is None:
            print(f"Error: Source with slug '{args.slug}' not found.", file=sys.stderr)
            sys.exit(1)

        # Enforce rule: ck_tryon_requires_mirror
        if args.tryon and source.image_policy != "mirror":
            print(
                f"Error: Cannot enable try-on (rights_tryon=true) for source '{args.slug}' with image_policy='{source.image_policy}'. "
                "Virtual try-on requires server-side mirrored images (image_policy='mirror').",
                file=sys.stderr,
            )
            sys.exit(1)

        today = date.today()
        source.status = "cleared"
        source.rights_display = bool(args.display)
        source.rights_tryon = bool(args.tryon)
        source.terms_checked_on = today

        evidence_note = f"[Cleared on {today} with evidence: {args.evidence_url.strip()}]"
        if source.notes:
            source.notes = f"{source.notes}\n{evidence_note}"
        else:
            source.notes = evidence_note

        await session.commit()
        print(f"Successfully CLEARED source '{args.slug}' ({source.name}).")
        print(f"  Status: {source.status}")
        print(f"  Rights Display: {source.rights_display}")
        print(f"  Rights Try-On: {source.rights_tryon}")
        print(f"  Image Policy: {source.image_policy}")
        print(f"  Terms Checked On: {source.terms_checked_on}")
        print(f"  Evidence: {args.evidence_url.strip()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clear a catalog source with mandatory written evidence.")
    parser.add_argument("slug", help="Slug of the catalog source to clear")
    parser.add_argument("--evidence-url", required=True, help="Link to written agreement, email, or evidence doc")
    parser.add_argument("--display", action="store_true", help="Grant rights to display images in consumer UI")
    parser.add_argument("--tryon", action="store_true", help="Grant rights to process images for AI virtual try-on")

    args = parser.parse_args()
    asyncio.run(clear_source(args))


if __name__ == "__main__":
    main()
