#!/usr/bin/env python3
"""Check nearest-neighbour category purity for embedded garments.

Computes the fraction of each garment's 5 nearest neighbours (cosine similarity)
that share the same category, comparing it with random chance:
    chance = sum((count_c / total)^2)

Usage:
    python scripts/catalog/check_neighbour_purity.py
"""

from __future__ import annotations

import asyncio
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.catalog import CanonicalGarment, GarmentEnrichment
from fashx.core.database import get_session_factory


async def evaluate_neighbour_purity(
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> dict[str, Any]:
    if session_factory is None:
        session_factory = get_session_factory()

    async with session_factory() as session:
        stmt = (
            select(CanonicalGarment.id, CanonicalGarment.display_name, CanonicalGarment.category, GarmentEnrichment.embedding)
            .join(GarmentEnrichment, GarmentEnrichment.garment_id == CanonicalGarment.id)
            .where(GarmentEnrichment.embedding.is_not(None))
        )
        rows = (await session.execute(stmt)).all()

        if len(rows) < 6:
            print(f"Need at least 6 embedded garments to evaluate 5 nearest neighbours (found {len(rows)}).")
            return {"count": len(rows), "purity": 0.0, "chance": 0.0}

        titles = [r[1] or "Unknown" for r in rows]
        cats = [r[2] for r in rows]
        vectors = [r[3] for r in rows]

        E = np.array(vectors, dtype=np.float32)
        norm = np.linalg.norm(E, axis=1, keepdims=True)
        norm[norm == 0] = 1.0
        E /= norm

        S = E @ E.T
        np.fill_diagonal(S, -1.0)

        k = min(5, len(cats) - 1)
        top = np.argsort(-S, axis=1)[:, :k]

        purity = float(np.mean([[cats[j] == cats[i] for j in top[i]] for i in range(len(cats))]))
        _, counts = np.unique(cats, return_counts=True)
        chance = float(((counts / counts.sum()) ** 2).sum())

        print(f"Garments evaluated: {len(cats)}")
        print(f"Neighbour purity: {purity:.2f} vs chance: {chance:.2f}")

        # Eyeball up to 5 garments with their neighbours
        eyeball_count = min(5, len(cats))
        eyeball_results = []
        print("\n--- Nearest Neighbour Inspection (5 items) ---")
        for i in range(eyeball_count):
            item_info = {
                "title": titles[i],
                "category": cats[i],
                "neighbours": [
                    {"title": titles[j], "category": cats[j], "similarity": float(S[i, j])}
                    for j in top[i]
                ],
            }
            eyeball_results.append(item_info)
            print(f"[{i+1}] {titles[i]} ({cats[i]}):")
            for n in item_info["neighbours"]:
                print(f"    -> {n['title']} ({n['category']}) [sim: {n['similarity']:.3f}]")

        return {
            "count": len(cats),
            "purity": purity,
            "chance": chance,
            "eyeball": eyeball_results,
        }


def main() -> None:
    asyncio.run(evaluate_neighbour_purity())


if __name__ == "__main__":
    main()
