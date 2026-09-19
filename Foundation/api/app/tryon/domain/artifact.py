from __future__ import annotations

from hashlib import sha256
from uuid import UUID


def compute_artifact_key(
    *,
    photo_id: UUID,
    photo_version: int,
    garment_id: UUID,
    garment_version: int,
    model_version: str,
    pipeline_version: str,
    configuration_hash: str = "default",
) -> str:
    canonical = "|".join(
        [
            str(photo_id),
            str(photo_version),
            str(garment_id),
            str(garment_version),
            model_version,
            pipeline_version,
            configuration_hash,
        ]
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
