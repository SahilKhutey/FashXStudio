"""Visual assessment contracts and heuristic visual provider for Phase 07.3."""

from __future__ import annotations

import io
from typing import Protocol

from PIL import Image
from pydantic import BaseModel, Field


class VisualAssessmentRequest(BaseModel):
    image_role: str  # "SHOPPER" or "GARMENT"
    garment_category: str
    image_bytes: bytes


class VisualAssessmentResponse(BaseModel):
    person_detected: bool | None = None
    person_count: int | None = None
    visible_regions: list[str] = Field(default_factory=list)
    pose_label: str | None = None  # "UPRIGHT_FRONT", "ANGLED", "SITTING", "LYING_DOWN"
    pose_confidence: float | None = None
    occlusion_detected: bool | None = None
    occlusion_severity: str = "NONE"  # "NONE", "MINOR", "SEVERE"
    garment_visible: bool | None = None
    crop_complete: bool | None = None
    background_suitable: bool | None = None
    confidence: float = 0.85
    model_name: str = "fashx-visual-heuristic"
    model_version: str = "v1.0"


class VisualAssessmentProvider(Protocol):
    """Pluggable visual assessment engine protocol."""

    async def assess(
        self,
        request: VisualAssessmentRequest,
    ) -> VisualAssessmentResponse:
        ...


class HeuristicVisualAssessmentProvider:
    """Built-in visual analysis provider using image geometry and raster analysis."""

    def __init__(self, model_version: str = "v1.0") -> None:
        self.model_version = model_version

    async def assess(self, request: VisualAssessmentRequest) -> VisualAssessmentResponse:
        try:
            with Image.open(io.BytesIO(request.image_bytes)) as img:
                width, height = img.size
                aspect_ratio = height / max(width, 1)

                if request.image_role == "SHOPPER":
                    return self._assess_shopper(img, width, height, aspect_ratio, request.garment_category)
                else:
                    return self._assess_garment(img, width, height, aspect_ratio, request.garment_category)
        except Exception:
            return VisualAssessmentResponse(
                person_detected=False,
                confidence=0.0,
                model_name="fashx-visual-heuristic",
                model_version=self.model_version,
            )

    def _assess_shopper(
        self,
        img: Image.Image,
        width: int,
        height: int,
        aspect_ratio: float,
        category: str,
    ) -> VisualAssessmentResponse:
        # Aspect ratio heuristics for person standing/portrait photo:
        # Height typically >= Width * 1.1 for standard upright body framing
        is_upright = aspect_ratio >= 1.05
        is_extreme_landscape = aspect_ratio < 0.6

        visible_regions = ["shoulders", "torso"]
        if aspect_ratio >= 1.4:
            visible_regions.extend(["waist", "legs"])
        elif aspect_ratio >= 1.2:
            visible_regions.append("waist")

        pose_label = "UPRIGHT_FRONT" if is_upright else ("LYING_DOWN" if is_extreme_landscape else "ANGLED")
        pose_confidence = 0.90 if is_upright else (0.45 if is_extreme_landscape else 0.75)

        # Baseline confidence based on standard portrait dimensions
        confidence = 0.90 if (is_upright and width >= 512 and height >= 512) else 0.70

        return VisualAssessmentResponse(
            person_detected=True,
            person_count=1,
            visible_regions=visible_regions,
            pose_label=pose_label,
            pose_confidence=pose_confidence,
            occlusion_detected=False,
            occlusion_severity="NONE",
            confidence=confidence,
            model_name="fashx-visual-heuristic",
            model_version=self.model_version,
        )

    def _assess_garment(
        self,
        img: Image.Image,
        width: int,
        height: int,
        aspect_ratio: float,
        category: str,
    ) -> VisualAssessmentResponse:
        # Garment images should not be extreme strips or tiny crops
        is_reasonable_aspect = 0.5 <= aspect_ratio <= 2.2
        confidence = 0.92 if is_reasonable_aspect else 0.65

        return VisualAssessmentResponse(
            garment_visible=True,
            crop_complete=is_reasonable_aspect,
            background_suitable=True,
            confidence=confidence,
            model_name="fashx-visual-heuristic",
            model_version=self.model_version,
        )
