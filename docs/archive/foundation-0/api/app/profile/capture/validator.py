import io
from dataclasses import dataclass, field

from PIL import Image, ImageStat
from schemas.common.enums import PhotoStatus


@dataclass
class QualityValidationResult:
    passed: bool
    status: PhotoStatus
    reject_reason: str | None = None
    metrics: dict[str, float] = field(default_factory=dict)


class PhotoQualityValidator:
    """Pre-inference quality gate validating user portraits before GPU queueing (Rule I07).

    Validates:
    1. Valid decodable image format (JPEG/PNG).
    2. Minimum resolution (>= 512x512).
    3. Aspect ratio: portrait framing (width/height between 0.45 and 1.25).
    4. Exposure: rejects underexposed (< 40) or overexposed (> 220) images.
    5. Contrast: minimum luminance standard deviation (>= 20.0).
    """

    MIN_WIDTH = 512
    MIN_HEIGHT = 512
    MIN_ASPECT = 0.45
    MAX_ASPECT = 1.25
    MIN_MEAN_LUMINANCE = 40.0
    MAX_MEAN_LUMINANCE = 220.0
    MIN_CONTRAST_STD = 15.0

    @classmethod
    def validate_photo_bytes(cls, photo_bytes: bytes) -> QualityValidationResult:
        try:
            img = Image.open(io.BytesIO(photo_bytes))
        except Exception:
            return QualityValidationResult(
                passed=False,
                status=PhotoStatus.REJECTED,
                reject_reason="Invalid or unreadable image file. Please upload a standard JPEG or PNG photo.",
            )

        w, h = img.size
        aspect_ratio = round(w / h, 3)

        # 1. Resolution Check
        if w < cls.MIN_WIDTH or h < cls.MIN_HEIGHT:
            return QualityValidationResult(
                passed=False,
                status=PhotoStatus.REJECTED,
                reject_reason=(
                    f"Photo resolution ({w}x{h}) is below the required {cls.MIN_WIDTH}x{cls.MIN_HEIGHT}. "
                    "Please upload a higher-resolution portrait photo."
                ),
                metrics={"width": float(w), "height": float(h), "aspect_ratio": aspect_ratio},
            )

        # 2. Aspect Ratio / Framing Check (Portrait Framing)
        if aspect_ratio > cls.MAX_ASPECT:
            return QualityValidationResult(
                passed=False,
                status=PhotoStatus.REJECTED,
                reject_reason=(
                    f"Landscape orientation detected (aspect ratio {aspect_ratio:.2f}). "
                    "Please upload a vertical, portrait-oriented photo."
                ),
                metrics={"width": float(w), "height": float(h), "aspect_ratio": aspect_ratio},
            )

        # 3. Luminance and Contrast Check
        grayscale = img.convert("L")
        stat = ImageStat.Stat(grayscale)
        mean_lum = round(stat.mean[0], 1)
        std_lum = round(stat.stddev[0], 1)

        metrics = {
            "width": float(w),
            "height": float(h),
            "aspect_ratio": aspect_ratio,
            "mean_luminance": mean_lum,
            "contrast_std": std_lum,
        }

        if mean_lum < cls.MIN_MEAN_LUMINANCE:
            return QualityValidationResult(
                passed=False,
                status=PhotoStatus.REJECTED,
                reject_reason=(
                    f"Photo is too dark (mean brightness {mean_lum} < {cls.MIN_MEAN_LUMINANCE}). "
                    "Please retake in a well-lit environment with front-facing light."
                ),
                metrics=metrics,
            )

        if mean_lum > cls.MAX_MEAN_LUMINANCE:
            return QualityValidationResult(
                passed=False,
                status=PhotoStatus.REJECTED,
                reject_reason=(
                    f"Photo is overexposed (mean brightness {mean_lum} > {cls.MAX_MEAN_LUMINANCE}). "
                    "Please avoid harsh direct flash or heavy backlight."
                ),
                metrics=metrics,
            )

        if std_lum < cls.MIN_CONTRAST_STD:
            return QualityValidationResult(
                passed=False,
                status=PhotoStatus.REJECTED,
                reject_reason=(
                    f"Photo has insufficient contrast (contrast {std_lum} < {cls.MIN_CONTRAST_STD}). "
                    "Ensure subject is clearly distinct from background."
                ),
                metrics=metrics,
            )

        return QualityValidationResult(
            passed=True,
            status=PhotoStatus.ACCEPTED,
            reject_reason=None,
            metrics=metrics,
        )
