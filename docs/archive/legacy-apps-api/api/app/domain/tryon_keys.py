"""
Pure Domain Logic: Try-On Artifact Key Computation
"""

import hashlib


def compute_tryon_artifact_key(
    user_photo_version_hash: str,
    canonical_garment_version: int,
    model_adapter_id: str,
    model_weights_version: str,
    preprocessing_version: str,
    render_config_hash: str,
) -> str:
    """
    Computes a deterministic content-addressed SHA-256 key for a try-on artifact.
    Ensures that any change to the model, preprocessing, garment, or photo
    automatically invalidates stale renders.
    """
    payload = (
        f"{user_photo_version_hash}:"
        f"{canonical_garment_version}:"
        f"{model_adapter_id}:"
        f"{model_weights_version}:"
        f"{preprocessing_version}:"
        f"{render_config_hash}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
