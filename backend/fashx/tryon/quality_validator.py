import io
import math
from typing import Any

from PIL import Image, UnidentifiedImageError

from .ports import PostInferenceValidationResult


class PostInferenceQualityValidator:
    """Structural safety and basic image-quality gate for VTO artifacts.
    This does not claim to measure garment-fit accuracy or identity similarity.
    """

    MIN_LUMINANCE = 25.0
    MAX_LUMINANCE = 235.0
    MIN_CONTRAST_STD = 12.0
    MIN_DIMENSION = 256
    MAX_SIDE = 4096
    MAX_PIXELS = 20_000_000
    MAX_BYTES = 15 * 1024 * 1024
    ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

    @classmethod
    def validate(cls, rendered_image_bytes: bytes) -> PostInferenceValidationResult:
        def reject(reason: str, **diagnostics: Any) -> PostInferenceValidationResult:
            return PostInferenceValidationResult(
                is_acceptable=False,
                structural_score=0.0,
                contrast_score=0.0,
                mean_luminance=0.0,
                failure_reason=reason,
                diagnostics=diagnostics,
            )

        if not rendered_image_bytes:
            return reject("Empty image payload")

        if len(rendered_image_bytes) > cls.MAX_BYTES:
            return reject(
                "Image payload exceeds maximum allowed size",
                size_bytes=len(rendered_image_bytes),
                max_bytes=cls.MAX_BYTES,
            )

        try:
            # 1. Structural integrity verification
            with Image.open(io.BytesIO(rendered_image_bytes)) as img_verify:
                img_verify.verify()

            # 2. Re-open to read format, dimensions, pixels
            with Image.open(io.BytesIO(rendered_image_bytes)) as img:
                img_format = img.format
                if img_format not in cls.ALLOWED_FORMATS:
                    return reject(
                        f"Unsupported image format: {img_format}",
                        format=img_format,
                        allowed=list(cls.ALLOWED_FORMATS),
                    )

                width, height = img.size
                if width < cls.MIN_DIMENSION or height < cls.MIN_DIMENSION:
                    return reject(
                        "Rendered image resolution below minimum threshold",
                        width=width,
                        height=height,
                        min_dimension=cls.MIN_DIMENSION,
                    )

                if width > cls.MAX_SIDE or height > cls.MAX_SIDE:
                    return reject(
                        f"Rendered image dimension exceeds maximum allowed side ({cls.MAX_SIDE}px)",
                        width=width,
                        height=height,
                        max_side=cls.MAX_SIDE,
                    )

                pixel_count = width * height
                if pixel_count > cls.MAX_PIXELS:
                    return reject(
                        f"Rendered image pixel count exceeds maximum limit ({cls.MAX_PIXELS} pixels)",
                        pixels=pixel_count,
                        max_pixels=cls.MAX_PIXELS,
                    )

                # Convert to grayscale for luminance & contrast metrics
                gray = img.convert("L")
                pixels = list(gray.tobytes())
                n = len(pixels)
                if n == 0:
                    return reject("Empty pixel buffer")

                mean_lum = sum(pixels) / n
                variance = sum((p - mean_lum) ** 2 for p in pixels) / n
                contrast_std = math.sqrt(variance)

                # Check extreme exposure / blank frames
                if mean_lum < cls.MIN_LUMINANCE:
                    return PostInferenceValidationResult(
                        is_acceptable=False,
                        structural_score=0.2,
                        contrast_score=contrast_std,
                        mean_luminance=mean_lum,
                        failure_reason="Render collapsed into underexposed / black frame",
                        diagnostics={"mean_lum": mean_lum, "std": contrast_std},
                    )

                if mean_lum > cls.MAX_LUMINANCE:
                    return PostInferenceValidationResult(
                        is_acceptable=False,
                        structural_score=0.2,
                        contrast_score=contrast_std,
                        mean_luminance=mean_lum,
                        failure_reason="Render blown out / overexposed white frame",
                        diagnostics={"mean_lum": mean_lum, "std": contrast_std},
                    )

                # Check low contrast / flat degenerate frame
                if contrast_std < cls.MIN_CONTRAST_STD:
                    return PostInferenceValidationResult(
                        is_acceptable=False,
                        structural_score=0.3,
                        contrast_score=contrast_std,
                        mean_luminance=mean_lum,
                        failure_reason="Render lacks contrast / solid flat artifact",
                        diagnostics={"contrast_std": contrast_std},
                    )

                # Structural confidence score based on healthy luminance and contrast
                norm_lum = 1.0 - abs(mean_lum - 128.0) / 128.0
                norm_cont = min(contrast_std / 50.0, 1.0)
                structural_score = round(0.5 * norm_lum + 0.5 * norm_cont, 3)

                return PostInferenceValidationResult(
                    is_acceptable=True,
                    structural_score=structural_score,
                    contrast_score=round(contrast_std, 2),
                    mean_luminance=round(mean_lum, 2),
                    failure_reason=None,
                    diagnostics={
                        "structural_score": structural_score,
                        "mean_lum": round(mean_lum, 2),
                        "contrast_std": round(contrast_std, 2),
                        "width": width,
                        "height": height,
                        "format": img_format,
                        "size_bytes": len(rendered_image_bytes),
                    },
                )

        except (UnidentifiedImageError, OSError) as exc:
            return reject(f"Image decoding error: {exc}", error=str(exc))
        except Exception as exc:
            return reject(f"Image validation unexpected error: {exc}", error=str(exc))
