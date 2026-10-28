#!/usr/bin/env python3
"""Batch embed catalog garments using Marqo-FashionCLIP or FakeEmbedder.

Loads primary images from storage, computes 512-dim normalized vectors in batches of 8,
and records the vector and embedding_model on garment_enrichments.

Usage:
    python scripts/catalog/embed_garments.py --dry-run
    python scripts/catalog/embed_garments.py --apply
    python scripts/catalog/embed_garments.py --fake --apply  # for tests/dev without downloading weights
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CanonicalGarment, GarmentEnrichment, GarmentImage
from fashx.catalog.embeddings.fake import FakeEmbedder
from fashx.catalog.embeddings.marqo_fashionclip import MarqoFashionClipEmbedder
from fashx.catalog.embeddings.ports import validate_embedding_vector
from fashx.catalog.embeddings.protocol import ImageEmbedder
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage


async def embed_garments(
    apply: bool = False,
    batch_size: int = 8,
    use_fake: bool = False,
    embedder: ImageEmbedder | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    storage: Any | None = None,
) -> int:
    if session_factory is None:
        session_factory = get_session_factory()
    if storage is None:
        storage = get_storage()

    if embedder is None:
        if use_fake:
            embedder = FakeEmbedder()
        else:
            try:
                embedder = MarqoFashionClipEmbedder()
            except ImportError as e:
                print(
                    f"Error: {e}\n"
                    "PyTorch / open_clip not installed. Run 'pip install .[ml]' or pass --fake for test mode.",
                    file=sys.stderr,
                )
                sys.exit(1)

    target_model = embedder.model_id
    print(f"Using embedder: {target_model} (dim={embedder.dim})")
    print(f"Mode: {'APPLY (writing to database)' if apply else 'DRY-RUN (no changes written)'}\n")

    async with session_factory() as session:
        # Find canonical garments whose enrichment has missing or different embedding_model
        stmt = (
            select(CanonicalGarment, GarmentEnrichment, GarmentImage)
            .outerjoin(GarmentEnrichment, GarmentEnrichment.garment_id == CanonicalGarment.id)
            .join(GarmentImage, GarmentImage.garment_id == CanonicalGarment.id)
            .where(
                or_(
                    GarmentEnrichment.id.is_(None),
                    GarmentEnrichment.embedding.is_(None),
                    GarmentEnrichment.embedding_model.is_(None),
                    GarmentEnrichment.embedding_model != target_model,
                )
            )
            .order_by(CanonicalGarment.created_at)
        )

        rows = (await session.execute(stmt)).all()
        # Group by garment_id to pick primary image
        items_to_embed: list[dict[str, Any]] = []
        seen_garments: set[Any] = set()

        for g, enr, img in rows:
            if g.id in seen_garments:
                continue
            seen_garments.add(g.id)
            items_to_embed.append({"garment": g, "enrichment": enr, "image": img})

        print(f"Found {len(items_to_embed)} garments needing embedding with model '{target_model}'.")
        if not items_to_embed:
            return 0

        embedded_count = 0
        for i in range(0, len(items_to_embed), batch_size):
            chunk = items_to_embed[i : i + batch_size]
            images_bytes: list[bytes] = []
            valid_chunk: list[dict[str, Any]] = []

            for item in chunk:
                key = item["image"].storage_key
                data = storage.get(key)
                if data is None:
                    print(f"  Warning: Image storage key '{key}' not found in storage. Skipping garment {item['garment'].id}.")
                    continue
                images_bytes.append(data)
                valid_chunk.append(item)

            if not valid_chunk:
                continue

            if apply:
                vectors = embedder.embed_images(images_bytes)
                for item, vec in zip(valid_chunk, vectors, strict=True):
                    validate_embedding_vector(vec, expected_dim=embedder.dim)
                    g = item["garment"]
                    enr = item["enrichment"]
                    img = item["image"]
                    if enr is None:
                        enr = GarmentEnrichment(
                            garment_id=g.id,
                            image_id=img.id,
                            model_version="1.0",
                            embedding_model=target_model,
                            attributes_json={},
                            embedding=vec,
                            confidence_summary={"source": "embed_garments"},
                        )
                        session.add(enr)
                    else:
                        enr.embedding = vec
                        enr.embedding_model = target_model
                    embedded_count += 1
                await session.flush()
                print(f"  [APPLY] Embedded batch {i // batch_size + 1} ({len(valid_chunk)} garments)")
            else:
                embedded_count += len(valid_chunk)
                print(f"  [DRY-RUN] Would embed batch {i // batch_size + 1} ({len(valid_chunk)} garments)")

        if apply:
            await session.commit()
            print(f"\nSuccessfully embedded {embedded_count} garments with model '{target_model}'.")
        else:
            print(f"\nDry-run complete. {embedded_count} garments ready to embed.")

        return embedded_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch embed garments in catalog")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for embedding (default: 8)")
    parser.add_argument("--fake", action="store_true", help="Use deterministic FakeEmbedder (no model download)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True, help="Simulate run without writing changes")
    group.add_argument("--apply", action="store_true", help="Apply embeddings to database")

    args = parser.parse_args()
    asyncio.run(
        embed_garments(
            apply=bool(args.apply),
            batch_size=args.batch_size,
            use_fake=bool(args.fake),
        )
    )


if __name__ == "__main__":
    main()
