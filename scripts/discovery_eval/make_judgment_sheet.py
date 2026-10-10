"""Generate blind judgment contact sheets and evaluation judgment CSV (Step 7.5)."""

import argparse
import csv
import pathlib
from typing import Any

from eval.persona_to_context import load_personas
from fashx.discovery.pipeline import rank

RUBRIC_HTML = """
<div style="background:#f8f9fa; border:1px solid #dee2e6; padding:15px; border-radius:6px; margin-bottom:20px; font-family:sans-serif;">
  <h3>Rating Rubric (0 - 3)</h3>
  <ul>
    <li><b>3:</b> Would love or buy this for this persona (Exceptional alignment)</li>
    <li><b>2:</b> Good, fits the brief (Relevant style, budget, and occasion)</li>
    <li><b>1:</b> Meh or off-style, but not wrong (Marginally relevant)</li>
    <li><b>0:</b> Wrong (Wrong gender, size, occasion, or plainly inappropriate)</li>
  </ul>
</div>
"""


def generate_judgment_sheets(rankers: list[str], personas_path: str = "eval/personas.yml") -> None:
    personas = load_personas(personas_path)

    judgments_csv_path = pathlib.Path("eval/judgments.csv")
    existing_judgments: set[tuple[str, str]] = set()
    if judgments_csv_path.exists():
        with open(judgments_csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                existing_judgments.add((r["persona_id"], r["garment_id"]))

    sheets_dir = pathlib.Path("eval/sheets")
    sheets_dir.mkdir(parents=True, exist_ok=True)

    to_judge_rows: list[dict[str, Any]] = []

    for ctx in personas:
        seen_garment_ids: set[str] = set()
        persona_garments: list[dict[str, Any]] = []

        # Union of top-25 across rankers
        for r_name in rankers:
            top_items = rank(ctx, page=0, limit=25, ranker=r_name)
            for it in top_items:
                g_id_str = str(it.id)
                if g_id_str not in seen_garment_ids:
                    seen_garment_ids.add(g_id_str)
                    persona_garments.append({
                        "id": g_id_str,
                        "title": it.title,
                        "brand": it.brand,
                        "price": it.price,
                        "sizes": ", ".join(it.sizes_in_stock),
                        "image_url": it.image_url,
                        "score": it.score,
                    })

                    if (ctx.id, g_id_str) not in existing_judgments:
                        to_judge_rows.append({
                            "persona_id": ctx.id,
                            "garment_id": g_id_str,
                            "rating": "",
                        })

        # Generate HTML contact sheet for persona
        cards_html = []
        for g in persona_garments:
            cards_html.append(f"""
            <div style="display:inline-block; vertical-align:top; width:220px; border:1px solid #ccc; border-radius:6px; margin:10px; padding:10px; font-family:sans-serif;">
              <img src="{g['image_url']}" alt="{g['title']}" style="width:100%; height:260px; object-fit:cover; border-radius:4px; background:#eee;" onerror="this.src='https://via.placeholder.com/220x260?text=Apparel';" />
              <h4 style="margin:8px 0 4px 0; font-size:14px; height:36px; overflow:hidden;">{g['title']}</h4>
              <p style="margin:2px 0; color:#555; font-size:12px;"><b>Brand:</b> {g['brand']}</p>
              <p style="margin:2px 0; color:#2e7d32; font-weight:bold; font-size:13px;">₹{g['price']:.0f}</p>
              <p style="margin:2px 0; color:#777; font-size:11px;"><b>Sizes:</b> {g['sizes']}</p>
              <div style="margin-top:8px;">
                <label style="font-size:12px; font-weight:bold;">Rating (0-3):</label>
                <input type="number" min="0" max="3" style="width:40px; margin-left:5px;" />
              </div>
            </div>
            """)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Judgment Contact Sheet - {ctx.name} ({ctx.id})</title>
</head>
<body style="padding:20px; font-family:sans-serif;">
  <h2>Persona Brief: {ctx.name} (<code>{ctx.id}</code>)</h2>
  <p><b>Gender:</b> {ctx.gender} | <b>Sizes:</b> {', '.join(ctx.sizes)} | <b>Budget:</b> ₹{ctx.budget_min} - ₹{ctx.budget_max} | <b>Occasion:</b> {ctx.occasion} | <b>Monk Tone:</b> {ctx.monk}</p>
  <p><b>Styles:</b> {', '.join(ctx.styles)} | <b>Liked Colors:</b> {', '.join(ctx.liked_colors)} | <b>Avoid:</b> {', '.join(ctx.avoided_colors)}</p>
  {RUBRIC_HTML}
  <hr/>
  <div>
    {''.join(cards_html)}
  </div>
</body>
</html>
"""
        sheet_path = sheets_dir / f"{ctx.id}.html"
        sheet_path.write_text(html_content, encoding="utf-8")

    # Write to_judge.csv
    to_judge_path = pathlib.Path("eval/to_judge.csv")
    with open(to_judge_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["persona_id", "garment_id", "rating"])
        writer.writeheader()
        writer.writerows(to_judge_rows)

    print(f"Generated {len(personas)} contact sheets in {sheets_dir}/.")
    print(f"Exported {len(to_judge_rows)} unjudged pairs to {to_judge_path}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate blind judgment contact sheets.")
    parser.add_argument("--rankers", nargs="+", default=["baseline", "v1"], help="Ranker variants to pool")
    parser.add_argument("--personas", default="eval/personas.yml", help="Path to personas YAML file")
    args = parser.parse_args()

    generate_judgment_sheets(args.rankers, args.personas)


if __name__ == "__main__":
    main()
