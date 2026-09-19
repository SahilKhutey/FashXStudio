from __future__ import annotations

from dataclasses import dataclass

from workers.profile_photo.domain.validation import BasicPhotoValidator, PhotoValidationResult


@dataclass(frozen=True)
class ProcessedPhoto:
    result: PhotoValidationResult


class ProfilePhotoProcessor:
    def __init__(self, validator: BasicPhotoValidator | None = None) -> None:
        self.validator = validator or BasicPhotoValidator()

    def process(self, payload: bytes, *, photo_type: str) -> ProcessedPhoto:
        return ProcessedPhoto(self.validator.validate(payload, photo_type=photo_type))
