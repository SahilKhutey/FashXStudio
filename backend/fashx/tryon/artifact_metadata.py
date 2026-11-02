from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO

from PIL import Image


@dataclass(frozen=True)
class ArtifactMetadata:
    content_type: str
    extension: str
    width: int
    height: int
    size_bytes: int
    content_sha256: str


def inspect_artifact(data: bytes) -> ArtifactMetadata:
    if not data:
        raise ValueError("Artifact cannot be empty")
    with Image.open(BytesIO(data)) as image:
        image.verify()
    with Image.open(BytesIO(data)) as image:
        image_format = image.format
        width, height = image.size
    formats = {
        "PNG": ("image/png", ".png"),
        "JPEG": ("image/jpeg", ".jpg"),
        "WEBP": ("image/webp", ".webp"),
    }
    if image_format not in formats:
        raise ValueError(f"Unsupported artifact format: {image_format}")
    content_type, extension = formats[image_format]
    digest = sha256(data).hexdigest()
    return ArtifactMetadata(
        content_type=content_type,
        extension=extension,
        width=width,
        height=height,
        size_bytes=len(data),
        content_sha256=digest,
    )
