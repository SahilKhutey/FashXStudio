"""Image validation threshold and limit configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ImageValidationConfig(BaseModel):
    """Configuration limits and rules for VTO input image validation."""

    policy_version: str = "v1"
    allowed_formats: set[str] = {
        "JPEG",
        "PNG",
        "WEBP",
    }
    min_width: int = 512
    min_height: int = 512
    max_width: int = 4096
    max_height: int = 4096
    max_pixels: int = 20_000_000
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    visual_confidence_threshold: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
    )
    reject_multiple_people: bool = True
