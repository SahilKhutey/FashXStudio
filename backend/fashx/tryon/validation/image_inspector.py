"""Technical image inspection and normalization for Phase 07.3."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, ImageOps

from .config import ImageValidationConfig
from .error_codes import (
    FORMAT_UNSUPPORTED,
    IMAGE_CORRUPTED,
    IMAGE_TOO_LARGE,
    IMAGE_TOO_SMALL,
)


class ImageInspectionError(Exception):
    """Exception raised when technical validation of image bytes fails."""

    def __init__(self, code: str, detail: str | None = None) -> None:
        self.code = code
        self.detail = detail or code
        super().__init__(f"{code}: {self.detail}")


@dataclass(frozen=True)
class InspectedImage:
    """Normalized technical output of image inspection."""

    normalized_bytes: bytes
    detected_format: str
    width: int
    height: int
    original_size_bytes: int
    original_sha256: str
    normalized_sha256: str


class ImageInspector:
    """Validates container integrity, formats, dimensions, and normalizes EXIF orientation."""

    def __init__(self, config: ImageValidationConfig | None = None) -> None:
        self.config = config or ImageValidationConfig()
        # Enforce decompression bomb defense
        Image.MAX_IMAGE_PIXELS = self.config.max_pixels

    def inspect(self, raw: bytes) -> InspectedImage:
        """Inspect and normalize raw image bytes."""
        if not raw or len(raw) < 16:
            raise ImageInspectionError(IMAGE_CORRUPTED, "Empty or truncated image bytes")

        original_size = len(raw)
        if original_size > self.config.max_file_size_bytes:
            raise ImageInspectionError(
                IMAGE_TOO_LARGE,
                f"File size {original_size} exceeds maximum {self.config.max_file_size_bytes} bytes",
            )

        original_sha256 = hashlib.sha256(raw).hexdigest()

        try:
            with Image.open(io.BytesIO(raw)) as img:
                detected_format = (img.format or "").upper()
                if detected_format not in self.config.allowed_formats:
                    raise ImageInspectionError(
                        FORMAT_UNSUPPORTED,
                        f"Format '{detected_format}' not supported. Allowed: {self.config.allowed_formats}",
                    )

                # Check dimensions before decoding full buffer
                width, height = img.size
                if width < self.config.min_width or height < self.config.min_height:
                    raise ImageInspectionError(
                        IMAGE_TOO_SMALL,
                        f"Dimensions {width}x{height} below minimum {self.config.min_width}x{self.config.min_height}",
                    )

                if width > self.config.max_width or height > self.config.max_height:
                    raise ImageInspectionError(
                        IMAGE_TOO_LARGE,
                        f"Dimensions {width}x{height} exceed maximum {self.config.max_width}x{self.config.max_height}",
                    )

                if width * height > self.config.max_pixels:
                    raise ImageInspectionError(
                        IMAGE_TOO_LARGE,
                        f"Pixel count {width * height} exceeds limit {self.config.max_pixels}",
                    )

                # Decode pixels fully to detect truncated/corrupted streams
                try:
                    img.load()
                except Exception as exc:
                    raise ImageInspectionError(
                        IMAGE_CORRUPTED, f"Failed decoding image raster: {exc}"
                    ) from exc

                # Normalize EXIF camera orientation
                try:
                    transposed = ImageOps.exif_transpose(img)
                    if transposed is not None:
                        img = transposed
                except Exception:
                    pass

                # Convert to RGB (removing alpha channel or palette)
                rgb_img = img.convert("RGB")
                norm_width, norm_height = rgb_img.size

                # Re-encode to clean, stripped JPEG raster
                out_buf = io.BytesIO()
                rgb_img.save(out_buf, format="JPEG", quality=95, optimize=True)
                normalized_bytes = out_buf.getvalue()

        except ImageInspectionError:
            raise
        except Image.DecompressionBombError as dce:
            raise ImageInspectionError(
                IMAGE_TOO_LARGE, f"Image decompression bomb detected: {dce}"
            ) from dce
        except Exception as exc:
            raise ImageInspectionError(
                IMAGE_CORRUPTED, f"Unrecognized image container: {exc}"
            ) from exc

        normalized_sha256 = hashlib.sha256(normalized_bytes).hexdigest()

        return InspectedImage(
            normalized_bytes=normalized_bytes,
            detected_format=detected_format,
            width=norm_width,
            height=norm_height,
            original_size_bytes=original_size,
            original_sha256=original_sha256,
            normalized_sha256=normalized_sha256,
        )
