"""Image quality evaluation with distinct display and VTO suitability profiles."""

from __future__ import annotations

from typing import Any

from fashx.catalog.images.models import ImageQualityResult, InspectedImage, QualityScore


class ImageQualityValidator:
    """Evaluates image quality with separated profiles for catalog display and virtual try-on."""

    DISPLAY_MIN_DIMENSION = 400
    VTO_MIN_RECOMMENDED_DIMENSION = 768
    MIN_ASPECT_RATIO = 0.25  # height / width minimum
    MAX_ASPECT_RATIO = 3.5  # height / width maximum

    @classmethod
    def evaluate_display_profile(cls, inspected: InspectedImage) -> ImageQualityResult:
        """Evaluate suitability for catalog browsing and consumer UI display."""
        notes: dict[str, Any] = {
            "width": inspected.width,
            "height": inspected.height,
            "format": inspected.detected_format,
        }

        if (
            inspected.width < cls.DISPLAY_MIN_DIMENSION
            or inspected.height < cls.DISPLAY_MIN_DIMENSION
        ):
            return ImageQualityResult(
                score=QualityScore.REJECT,
                profile_name="display",
                passed=False,
                notes={"reason": "dimensions_below_display_minimum", **notes},
            )

        aspect_ratio = inspected.height / max(inspected.width, 1)
        notes["aspect_ratio"] = round(aspect_ratio, 2)

        if aspect_ratio < cls.MIN_ASPECT_RATIO or aspect_ratio > cls.MAX_ASPECT_RATIO:
            return ImageQualityResult(
                score=QualityScore.REVIEW,
                profile_name="display",
                passed=True,
                notes={"reason": "unusual_aspect_ratio", **notes},
            )

        return ImageQualityResult(
            score=QualityScore.PASS,
            profile_name="display",
            passed=True,
            notes=notes,
        )

    @classmethod
    def evaluate_vto_profile(
        cls,
        inspected: InspectedImage,
        vto_permitted: bool = False,
    ) -> ImageQualityResult:
        """Evaluate suitability for virtual try-on and garment segmentation."""
        if not vto_permitted:
            return ImageQualityResult(
                score=QualityScore.NOT_APPLICABLE,
                profile_name="vto",
                passed=False,
                notes={"reason": "vto_rights_not_granted"},
            )

        notes: dict[str, Any] = {
            "width": inspected.width,
            "height": inspected.height,
            "format": inspected.detected_format,
        }

        if (
            inspected.width < cls.DISPLAY_MIN_DIMENSION
            or inspected.height < cls.DISPLAY_MIN_DIMENSION
        ):
            return ImageQualityResult(
                score=QualityScore.REJECT,
                profile_name="vto",
                passed=False,
                notes={"reason": "dimensions_too_small_for_vto", **notes},
            )

        aspect_ratio = inspected.height / max(inspected.width, 1)
        notes["aspect_ratio"] = round(aspect_ratio, 2)

        # VTO typically requires portrait or square orientation (0.8 - 2.0)
        if aspect_ratio < 0.6 or aspect_ratio > 2.5:
            return ImageQualityResult(
                score=QualityScore.REVIEW,
                profile_name="vto",
                passed=False,
                notes={"reason": "vto_aspect_ratio_requires_review", **notes},
            )

        # Resolution check: recommended >= 768x768
        if (
            inspected.width < cls.VTO_MIN_RECOMMENDED_DIMENSION
            or inspected.height < cls.VTO_MIN_RECOMMENDED_DIMENSION
        ):
            return ImageQualityResult(
                score=QualityScore.REVIEW,
                profile_name="vto",
                passed=False,
                notes={"reason": "resolution_below_recommended_768px", **notes},
            )

        return ImageQualityResult(
            score=QualityScore.PASS,
            profile_name="vto",
            passed=True,
            notes=notes,
        )
