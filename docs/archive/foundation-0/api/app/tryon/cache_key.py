import hashlib
import json
from typing import Any
from uuid import UUID


def compute_tryon_cache_key(
    user_photo_hash: str,
    garment_id: UUID,
    garment_version: int,
    model_version: str,
    pipeline_version: str,
    render_config: dict[str, Any] | None = None,
) -> str:
    """Compute a deterministic SHA-256 composite cache key for try-on renders.

    Formula (Roadmap 4.4):
        SHA256(user_photo_hash + garment_id + garment_version + model_version + pipeline_version + sorted(render_config))
    """
    config_str = ""
    if render_config:
        config_str = json.dumps(render_config, sort_keys=True)

    raw_payload = (
        f"{user_photo_hash}:{garment_id}:{garment_version}:"
        f"{model_version}:{pipeline_version}:{config_str}"
    )
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
