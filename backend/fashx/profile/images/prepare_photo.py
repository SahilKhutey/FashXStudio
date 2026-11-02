from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, ImageOps, ImageStat

from fashx.profile.images.detector import (
    ConfiguredPersonDetector,
    PersonDetection,
    PersonDetector,
)


class PhotoPreparationError(Exception):
    """Raised when user photo preparation or normalization fails."""

    def __init__(self, message: str, code: str = "photo_preparation_failed") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass
class PreparedPhoto:
    image_bytes: bytes
    content_sha256: str
    width: int
    height: int
    image_format: str
    file_size_bytes: int
    has_person: bool
    has_face: bool
    quality_score: float
    framing_score: float
    pose_score: float
    ready_for_tryon: bool
    quality_reasons: list[str]
    detection: PersonDetection | None = None


class PersonPhotoPreparer:
    """Validates, normalizes, and prepares a user photo for virtual try-on.

    Responsibilities:
    1. Size and format bounds check (max 10MB).
    2. EXIF orientation correction via ImageOps.exif_transpose.
    3. RGB color mode normalization (compositing alpha transparency on white).
    4. Resolution bounds check (min 256x320, recommended 512x512).
    5. Max dimension downscaling (max side <= 1536px) with LANCZOS resampling.
    6. Aspect ratio and framing evaluation (portrait orientation).
    7. Exposure (mean luminance [40, 220]) and contrast (stddev >= 15.0) validation.
    8. JPEG encoding at quality 92 and SHA-256 content hashing.
    9. Person and pose suitability evaluation via PersonDetector.
    10. Overall quality score computation and ready_for_tryon decision.
    """

    MAX_INPUT_BYTES: int = 10 * 1024 * 1024  # 10 MB
    MAX_OUTPUT_SIDE: int = 1536
    MIN_WIDTH: int = 256
    MIN_HEIGHT: int = 320
    MIN_RECOMMENDED_WIDTH: int = 512
    MIN_RECOMMENDED_HEIGHT: int = 512

    MIN_ASPECT: float = 0.45
    MAX_ASPECT: float = 1.25
    OPTIMAL_ASPECT: float = 0.75  # 3:4 portrait

    MIN_MEAN_LUMINANCE: float = 40.0
    MAX_MEAN_LUMINANCE: float = 220.0
    MIN_CONTRAST_STD: float = 15.0

    def __init__(
        self,
        max_output_side: int = MAX_OUTPUT_SIDE,
        detector: PersonDetector | None = None,
    ) -> None:
        self.max_output_side = max_output_side
        self.detector = detector or ConfiguredPersonDetector()

    def prepare(
        self,
        raw_bytes: bytes,
        *,
        run_detector: bool = True,
    ) -> PreparedPhoto:
        if len(raw_bytes) > self.MAX_INPUT_BYTES:
            max_mb = self.MAX_INPUT_BYTES // (1024 * 1024)
            raise PhotoPreparationError(
                f"Photo payload exceeds maximum permitted size of {max_mb}MB",
                code="payload_too_large",
            )

        # 1. Open and verify image structure
        try:
            with Image.open(io.BytesIO(raw_bytes)) as probe:
                probe.verify()
        except Exception as exc:
            raise PhotoPreparationError(
                f"Corrupted or invalid image payload: {exc}",
                code="corrupted_image",
            ) from exc

        # 2. Reopen for processing (verify closes underlying stream)
        try:
            img = Image.open(io.BytesIO(raw_bytes))
        except Exception as exc:
            raise PhotoPreparationError(
                f"Failed to decode image payload: {exc}",
                code="decode_failed",
            ) from exc

        # 3. EXIF orientation correction
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # 4. Color mode conversion to RGB
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            rgba = img.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[3])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        w, h = img.size

        # 5. Minimum dimension check
        if w < self.MIN_WIDTH or h < self.MIN_HEIGHT:
            raise PhotoPreparationError(
                f"Photo resolution ({w}x{h}) is below the required minimum of {self.MIN_WIDTH}x{self.MIN_HEIGHT}",
                code="resolution_too_low",
            )

        quality_reasons: list[str] = []

        # 6. Framing / Aspect ratio check
        aspect = round(w / h, 3)
        if aspect > self.MAX_ASPECT:
            quality_reasons.append("landscape_orientation")
            framing_score = max(0.1, round(1.0 - (aspect - self.MAX_ASPECT) * 1.5, 2))
        elif aspect < self.MIN_ASPECT:
            quality_reasons.append("narrow_crop")
            framing_score = max(0.1, round(1.0 - (self.MIN_ASPECT - aspect) * 1.5, 2))
        else:
            framing_score = max(0.5, round(1.0 - abs(aspect - self.OPTIMAL_ASPECT) * 0.8, 2))

        # 7. Max output side scaling
        if max(w, h) > self.max_output_side:
            scale = self.max_output_side / max(w, h)
            new_w = max(1, int(round(w * scale)))
            new_h = max(1, int(round(h * scale)))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            w, h = img.size

        # 8. Exposure & Contrast heuristics
        gray = img.convert("L")
        stat = ImageStat.Stat(gray)
        mean_lum = round(float(stat.mean[0]), 1)
        std_lum = round(float(stat.stddev[0]), 1)

        if mean_lum < self.MIN_MEAN_LUMINANCE:
            quality_reasons.append("underexposed")
        elif mean_lum > self.MAX_MEAN_LUMINANCE:
            quality_reasons.append("overexposed")

        if std_lum < self.MIN_CONTRAST_STD:
            quality_reasons.append("low_contrast")

        # 9. Encode normalized JPEG
        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG", quality=92, optimize=True)
        jpeg_bytes = out_buf.getvalue()
        content_sha256 = hashlib.sha256(jpeg_bytes).hexdigest()

        # 10. Person detection
        detection: PersonDetection | None = None
        has_person = True
        has_face = False
        pose_score = 0.0

        if run_detector and self.detector is not None:
            detection = self.detector.detect(jpeg_bytes)
            if detection.person_count == 0:
                quality_reasons.append("no_person_detected")
                has_person = False
            elif detection.person_count > 1:
                quality_reasons.append("multiple_people_detected")
                has_person = False
            else:
                has_person = True

            has_face = detection.has_face
            pose_score = detection.pose_score
        else:
            has_person = True
            has_face = True
            pose_score = 0.85

        # 11. Calculate overall quality score [0.0, 1.0]
        lum_penalty = 0.0
        if mean_lum < self.MIN_MEAN_LUMINANCE:
            lum_penalty = min(0.4, (self.MIN_MEAN_LUMINANCE - mean_lum) / self.MIN_MEAN_LUMINANCE)
        elif mean_lum > self.MAX_MEAN_LUMINANCE:
            lum_penalty = min(0.4, (mean_lum - self.MAX_MEAN_LUMINANCE) / (255 - self.MAX_MEAN_LUMINANCE))

        contrast_penalty = 0.0
        if std_lum < self.MIN_CONTRAST_STD:
            contrast_penalty = min(0.3, (self.MIN_CONTRAST_STD - std_lum) / self.MIN_CONTRAST_STD)

        det_confidence = detection.confidence if detection else 0.85
        base_quality = 0.4 * framing_score + 0.3 * (1.0 - lum_penalty) + 0.3 * (1.0 - contrast_penalty)
        quality_score = max(0.0, min(1.0, round(base_quality * det_confidence, 2)))

        # 12. Determine ready_for_tryon
        fatal_issues = {
            "no_person_detected",
            "multiple_people_detected",
            "landscape_orientation",
            "underexposed",
            "overexposed",
        }
        has_fatal_issue = any(r in fatal_issues for r in quality_reasons)
        ready_for_tryon = has_person and not has_fatal_issue

        return PreparedPhoto(
            image_bytes=jpeg_bytes,
            content_sha256=content_sha256,
            width=w,
            height=h,
            image_format="JPEG",
            file_size_bytes=len(jpeg_bytes),
            has_person=has_person,
            has_face=has_face,
            quality_score=quality_score,
            framing_score=framing_score,
            pose_score=pose_score,
            ready_for_tryon=ready_for_tryon,
            quality_reasons=sorted(set(quality_reasons)),
            detection=detection,
        )
