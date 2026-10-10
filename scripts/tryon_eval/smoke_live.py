"""Manual live smoke test for FASHN API adapter (not run in automated CI)."""

import os
import sys
import time

from fashx.application.ports.tryon import TryOnError, TryOnRequest
from fashx.core.settings import get_settings
from fashx.infrastructure.tryon.fashn_api import FashnApiAdapter
from fashx.ml.prep import prepare_for_provider


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scripts/tryon_eval/smoke_live.py <person.jpg> <garment.jpg> [category]")
        sys.exit(1)

    s = get_settings()
    api_key = s.fashn_api_key.get_secret_value() if s.fashn_api_key else os.getenv("FASHN_API_KEY", "")
    if not api_key:
        print("Error: FASHN_API_KEY not configured in environment or settings.")
        sys.exit(1)

    ad = FashnApiAdapter(
        api_key=api_key,
        base_url=s.fashn_base_url,
        model=s.fashn_model,
        mode=s.fashn_mode,
        cost_usd_est=s.tryon_est_cost_usd,
    )

    with open(sys.argv[1], "rb") as f:
        person = f.read()
    with open(sys.argv[2], "rb") as f:
        garment = f.read()

    cat = sys.argv[3] if len(sys.argv) > 3 else "auto"
    req = TryOnRequest(
        person_jpeg=prepare_for_provider(person),
        garment_jpeg=prepare_for_provider(garment),
        category=cat,  # type: ignore[arg-type]
    )

    t0 = time.monotonic()
    try:
        out = ad.run(req)
        with open("smoke_out.png", "wb") as f:
            f.write(out.image_bytes)
        print(f"OK {out.provider_job_id} {time.monotonic() - t0:.1f}s")
    except TryOnError as e:
        print(f"ERR {e.code} retryable={e.retryable} detail={e.detail}")


if __name__ == "__main__":
    main()
