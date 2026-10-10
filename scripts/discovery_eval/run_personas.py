"""Run discovery ranking pipeline across evaluation personas and save ranked results."""

import argparse
import json
import pathlib

from eval.persona_to_context import load_personas
from fashx.discovery.pipeline import rank


def run_personas(ranker: str, personas_path: str, out_path: str, limit: int = 25) -> None:
    personas = load_personas(personas_path)
    results = {}

    for ctx in personas:
        ranked_items = rank(ctx, page=0, limit=limit, ranker=ranker)
        results[ctx.id] = {
            "persona_id": ctx.id,
            "name": ctx.name,
            "gender": ctx.gender,
            "monk": ctx.monk,
            "body_type": ctx.body_type,
            "cold_start": ctx.cold_start,
            "ranked_garments": [
                {
                    "id": str(it.id),
                    "title": it.title,
                    "brand": it.brand,
                    "source_id": str(it.source_id),
                    "category": it.category,
                    "sub_category": it.sub_category,
                    "price": it.price,
                    "sizes_in_stock": it.sizes_in_stock,
                    "score": it.score,
                    "reasons": it.reasons,
                    "relaxed": it.relaxed,
                }
                for it in ranked_items
            ],
        }

    out_file = pathlib.Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Successfully evaluated {len(personas)} personas using ranker '{ranker}'. Results saved to {out_file}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run discovery ranking across evaluation personas.")
    parser.add_argument("--ranker", default="v1", choices=["baseline", "v1", "v2"], help="Ranker variant to evaluate")
    parser.add_argument("--personas", default="eval/personas.yml", help="Path to personas YAML file")
    parser.add_argument("--limit", type=int, default=25, help="Number of items to retrieve per persona")
    parser.add_argument("--out", default=None, help="Output JSON path")
    args = parser.parse_args()

    out_file = args.out or f"eval_results/{args.ranker}.json"
    run_personas(args.ranker, args.personas, out_file, args.limit)


if __name__ == "__main__":
    main()
