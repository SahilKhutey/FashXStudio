import hashlib


def compute_tryon_cache_key(
    photo_version_hash: str,
    garment_version: int,
    model_version: str,
    pipeline_version: str,
    render_config_hash: str,
) -> str:
    payload = f"{photo_version_hash}:{garment_version}:{model_version}:{pipeline_version}:{render_config_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
