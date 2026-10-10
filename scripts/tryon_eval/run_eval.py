"""Offline / staging harness to run eval pairs through configured try-on providers."""

import csv
import json
import pathlib
import sys
import time

from fashx.application.ports.tryon import TryOnError, TryOnRequest
from fashx.core.settings import get_settings
from fashx.infrastructure.tryon.fashn_api import FashnApiAdapter
from fashx.ml.prep import prepare_for_provider
from fashx.tryon.adapters.mock_adapter import MockAdapter

ROOT = pathlib.Path("eval_data")
OUT = pathlib.Path("eval_results")


def main() -> None:
    if not (ROOT / "manifest.csv").exists():
        print("Note: eval_data/manifest.csv not found. Create manifest before running evaluation.")
        sys.exit(0)

    s = get_settings()
    providers = {}

    if s.fashn_api_key:
        providers["fashn_v16"] = FashnApiAdapter(
            api_key=s.fashn_api_key.get_secret_value(),
            base_url=s.fashn_base_url,
            model="tryon-v1.6",
            mode=s.fashn_mode,
            cost_usd_est=s.tryon_est_cost_usd,
        )
    else:
        providers["mock"] = MockAdapter()

    rows = list(csv.DictReader(open(ROOT / "manifest.csv", encoding="utf-8")))
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else set()

    for name, ad in providers.items():
        d = OUT / name
        d.mkdir(parents=True, exist_ok=True)
        log_path = OUT / f"{name}.jsonl"

        with open(log_path, "a", encoding="utf-8") as log_file:
            for r in rows:
                if only and r["pair_id"] not in only:
                    continue

                person_file = ROOT / r["person_file"]
                garment_file = ROOT / r["garment_file"]
                if not person_file.exists() or not garment_file.exists():
                    print(f"Skipping {r['pair_id']}: files missing")
                    continue

                req = TryOnRequest(
                    person_jpeg=prepare_for_provider(person_file.read_bytes()),
                    garment_jpeg=prepare_for_provider(garment_file.read_bytes()),
                    category=r.get("category", "auto"),  # type: ignore[arg-type]
                )

                t0 = time.monotonic()
                rec = {"pair_id": r["pair_id"], "provider": name}
                try:
                    out = ad.run(req)
                    (d / f"{r['pair_id']}.png").write_bytes(out.image_bytes)
                    rec.update(
                        {
                            "ok": True,
                            "latency_s": round(time.monotonic() - t0, 2),
                            "cost_usd": out.cost_usd_est,
                        }
                    )
                except TryOnError as e:
                    rec.update(
                        {
                            "ok": False,
                            "latency_s": round(time.monotonic() - t0, 2),
                            "error": e.code,
                            "retryable": e.retryable,
                        }
                    )

                log_file.write(json.dumps(rec) + "\n")
                log_file.flush()
                time.sleep(0.5)


if __name__ == "__main__":
    main()
