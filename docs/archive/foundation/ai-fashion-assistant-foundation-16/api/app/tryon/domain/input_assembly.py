from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from api.app.core.errors import ConflictError, NotFoundError

SUPPORTED_CATEGORIES = {"tops", "top", "dress", "dresses"}


@dataclass(frozen=True, slots=True)
class TryOnInputBundle:
    job_id: UUID
    user_id: UUID
    photo_id: UUID
    garment_id: UUID
    photo_key: str
    garment_image_key: str
    photo_version: int
    garment_version: int
    model_version: str
    pipeline_version: str


def validate_garment_for_tryon(*, category: str, image_key: str | None) -> None:
    if category.strip().lower() not in SUPPORTED_CATEGORIES:
        raise ConflictError("Garment category is not supported by the current VTO pipeline")
    if not image_key:
        raise NotFoundError("Garment has no try-on-compatible image")
