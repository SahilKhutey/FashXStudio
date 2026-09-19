from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO

from PIL import Image, ImageFile, UnidentifiedImageError

ImageFile.LOAD_TRUNCATED_IMAGES = False


@dataclass(frozen=True)
class ResultQuality:
    accepted: bool
    quality_score: float
    width: int
    height: int
    content_type: str
    size_bytes: int
    sha256: str
    reasons: tuple[str, ...]


def validate_result_bytes(
    content: bytes,
    *,
    declared_content_type: str | None,
    min_width: int,
    min_height: int,
    max_bytes: int,
) -> ResultQuality:
    reasons: list[str] = []
    digest = sha256(content).hexdigest()
    size = len(content)
    if size == 0:
        return ResultQuality(False, 0.0, 0, 0, "application/octet-stream", 0, digest, ("empty_result",))
    if size > max_bytes:
        reasons.append("result_too_large")

    content_type = (declared_content_type or "").split(";", 1)[0].lower()
    if not content_type.startswith("image/"):
        reasons.append("invalid_content_type")

    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
        with Image.open(BytesIO(content)) as image:
            width, height = image.size
            detected_type = Image.MIME.get(image.format, content_type or "application/octet-stream")
    except (UnidentifiedImageError, OSError, ValueError):
        return ResultQuality(False, 0.0, 0, 0, content_type or "application/octet-stream", size, digest, tuple(reasons + ["invalid_image"]))

    if width < min_width or height < min_height:
        reasons.append("result_resolution_too_low")

    ratio = width / height if height else 0.0
    if ratio < 0.2 or ratio > 2.5:
        reasons.append("result_aspect_ratio_invalid")

    score = 1.0
    if width < min_width or height < min_height:
        score -= 0.45
    if ratio < 0.3 or ratio > 2.2:
        score -= 0.15
    if not detected_type.startswith("image/"):
        score -= 0.25
    score = max(0.0, min(1.0, score))

    return ResultQuality(
        accepted=not reasons,
        quality_score=score,
        width=width,
        height=height,
        content_type=detected_type,
        size_bytes=size,
        sha256=digest,
        reasons=tuple(reasons),
    )
