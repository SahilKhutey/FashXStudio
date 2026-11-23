from __future__ import annotations

from uuid import UUID, uuid4


def new_upload_id() -> UUID:
    return uuid4()


def new_image_id() -> UUID:
    return uuid4()


def quarantine_key(
    environment: str,
    user_id: UUID,
    upload_id: UUID,
) -> str:
    return f"temporary/uploads/{environment}/{user_id}/{upload_id}/original"


def validated_image_key(
    user_id: UUID,
    image_id: UUID,
) -> str:
    return f"users/{user_id}/images/{image_id}/original.webp"
