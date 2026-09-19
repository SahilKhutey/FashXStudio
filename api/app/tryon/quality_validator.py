import io
import math

from PIL import Image

from .ports import PostInferenceValidationResult


class PostInferenceQualityValidator:
    """Rule I10: Post-Inference Quality Validation to prevent corrupted renders from reaching users."""

    MIN_LUMINANCE = 25.0
    MAX_LUMINANCE = 235.0
    MIN_CONTRAST_STD = 12.0
    MIN_DIMENSION = 256

    @classmethod
    def validate(cls, rendered_image_bytes: bytes) -> PostInferenceValidationResult:
        """Validate rendered try-on image for structural soundness and absence of render artifacts."""
        try:
            with Image.open(io.BytesIO(rendered_image_bytes)) as img:
                width, height = img.size
                if width < cls.MIN_DIMENSION or height < cls.MIN_DIMENSION:
                    return PostInferenceValidationResult(
                        is_acceptable=False,
                        structural_score=0.0,
                        contrast_score=0.0,
                        mean_luminance=0.0,
                        failure_reason="Rendered image resolution below minimum threshold",
                        diagnostics={"width": width, "height": height},
                    )

                # Convert to grayscale for luminance & contrast metrics
                gray = img.convert("L")
                pixels = list(gray.tobytes())
                n = len(pixels)
                if n == 0:
                    return PostInferenceValidationResult(
                        is_acceptable=False,
                        structural_score=0.0,
                        contrast_score=0.0,
                        mean_luminance=0.0,
                        failure_reason="Empty pixel buffer",
                    )

                mean_lum = sum(pixels) / n
                variance = sum((p - mean_lum) ** 2 for p in pixels) / n
                contrast_std = math.sqrt(variance)

                # Check 1: Extreme exposure / blank frames
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

                # Check 2: Low contrast / flat degenerate frame
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
                    diagnostics={"structural_score": structural_score},
                )

        except Exception as exc:
            return PostInferenceValidationResult(
                is_acceptable=False,
                structural_score=0.0,
                contrast_score=0.0,
                mean_luminance=0.0,
                failure_reason=f"Image decoding error: {exc}",
            )
