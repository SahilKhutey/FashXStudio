"""Generate randomized blind rating sheets for independent human raters."""

import csv
import pathlib
import random
import uuid

OUT = pathlib.Path("eval_results")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    images = list(OUT.glob("*/*.png"))
    if not images:
        print("No eval result images found under eval_results/*/*.png.")
        return

    pairs = []
    for img_path in images:
        provider = img_path.parent.name
        pair_id = img_path.stem
        blind_code = f"C{uuid.uuid4().hex[:8].upper()}"
        pairs.append((blind_code, provider, pair_id, str(img_path)))

    random.shuffle(pairs)

    # 1. Blind rating sheet for volunteers / raters
    sheet_file = OUT / "rating_sheet.csv"
    with open(sheet_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "code",
                "image_path",
                "fidelity",
                "fit",
                "body_pose",
                "identity",
                "artifacts",
                "overall",
                "unacceptable",
                "notes",
            ]
        )
        for code, _, _, path in pairs:
            writer.writerow([code, path, "", "", "", "", "", "", "", ""])

    # 2. Secret code map (kept confidential from raters)
    map_file = OUT / "code_map.csv"
    with open(map_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "provider", "pair_id", "image_path"])
        for code, prov, pid, path in pairs:
            writer.writerow([code, prov, pid, path])

    print(f"Generated {sheet_file} ({len(pairs)} rows) and {map_file}.")


if __name__ == "__main__":
    main()
