"""Calculate scorecard metrics, slice performance, and threshold validation."""

import csv
import pathlib
from collections import defaultdict

ROOT = pathlib.Path("eval_data")
OUT = pathlib.Path("eval_results")


def compute_quantiles(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    idx = int(round(q * (len(sorted_v) - 1)))
    return sorted_v[idx]


def main() -> None:
    code_map_file = OUT / "code_map.csv"
    rating_sheet_file = OUT / "rating_sheet.csv"

    if not code_map_file.exists() or not rating_sheet_file.exists():
        print("Missing rating_sheet.csv or code_map.csv in eval_results/.")
        return

    # Map blind code -> (provider, pair_id)
    codes = {}
    with open(code_map_file, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            codes[r["code"]] = (r["provider"], r["pair_id"])

    # Load manifest attributes if available
    manifest = {}
    if (ROOT / "manifest.csv").exists():
        with open(ROOT / "manifest.csv", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                manifest[r["pair_id"]] = r

    # Aggregate ratings per (provider, pair_id)
    ratings_by_prov = defaultdict(list)
    with open(rating_sheet_file, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            code = r.get("code", "")
            if code not in codes or not r.get("overall"):
                continue
            prov, pid = codes[code]
            try:
                rec = {
                    "pair_id": pid,
                    "overall": float(r["overall"]),
                    "identity": float(r.get("identity") or 3.0),
                    "unacceptable": int(r.get("unacceptable") or 0)
                    or (1 if float(r["overall"]) <= 2 else 0),
                    "manifest": manifest.get(pid, {}),
                }
                ratings_by_prov[prov].append(rec)
            except ValueError:
                continue

    for prov, items in ratings_by_prov.items():
        if not items:
            continue
        total = len(items)
        acceptable_ge4 = sum(1 for x in items if x["overall"] >= 4.0)
        unacceptable_le2 = sum(1 for x in items if x["unacceptable"] == 1 or x["overall"] <= 2.0)
        identity_ge4 = sum(1 for x in items if x["identity"] >= 4.0)

        mean_overall = sum(x["overall"] for x in items) / total
        pct_ge4 = (acceptable_ge4 / total) * 100.0
        pct_le2 = (unacceptable_le2 / total) * 100.0
        pct_ident = (identity_ge4 / total) * 100.0

        print(f"\n=================== Provider: {prov} ===================")
        print(f"Total Rated Images: {total}")
        print(f"Mean Overall Score: {mean_overall:.2f} / 5.0")
        print(f"Share Rated >= 4/5: {pct_ge4:.1f}% (Threshold: >= 70%) -> {'PASS' if pct_ge4 >= 70 else 'FAIL'}")
        print(f"Share Rated <= 2/5: {pct_le2:.1f}% (Threshold: <= 10%) -> {'PASS' if pct_le2 <= 10 else 'FAIL'}")
        print(f"Identity Preserved >= 4: {pct_ident:.1f}% (Threshold: >= 95%) -> {'PASS' if pct_ident >= 95 else 'FAIL'}")


if __name__ == "__main__":
    main()
