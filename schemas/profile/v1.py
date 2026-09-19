"""
Profile, Body, Measurements and Consent Domain Contracts v1
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import Field
from schemas.base import BaseContractModel


class ConsentScopeV1(BaseContractModel):
    granted: bool
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    ip_address_hash: Optional[str] = None


class UserConsentV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    user_id: str
    body_photo_processing: ConsentScopeV1 = Field(
        description="Allows ephemeral loading of portrait into GPU memory for VTO render."
    )
    measurement_extraction: ConsentScopeV1 = Field(
        description="Allows CV/VLM analysis of photo to estimate body proportions."
    )
    camera_stream_access: ConsentScopeV1 = Field(
        description="Allows live camera feed access in client app."
    )
    personalization_profiling: ConsentScopeV1 = Field(
        description="Allows logging save/reject events to rank home feed."
    )
    ml_model_training: ConsentScopeV1 = Field(
        default_factory=lambda: ConsentScopeV1(granted=False),
        description="EXPLICIT OPT-IN ONLY: Allows anonymized user portraits to fine-tune VTO weights.",
    )
    third_party_analytics: ConsentScopeV1 = Field(
        default_factory=lambda: ConsentScopeV1(granted=False)
    )
    updated_at: datetime


class MeasurementSource(str, Enum):
    USER_REPORTED = "user_reported"
    COMPUTER_VISION_ESTIMATED = "computer_vision_estimated"
    FIT_FEEDBACK_INFERRED = "fit_feedback_inferred"
    TAILOR_ENTERED = "tailor_entered"


class MeasurementType(str, Enum):
    HEIGHT = "height"
    CHEST = "chest"
    WAIST = "waist"
    HIP = "hip"
    INSEAM = "inseam"
    SHOULDER = "shoulder"
    NECK = "neck"
    ARM_LENGTH = "arm_length"


class MeasurementV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    measurement_id: str
    user_id: str
    measurement_type: MeasurementType
    value: float = Field(gt=0.0, description="Measurement numerical value")
    unit: str = Field(default="cm", pattern="^(cm|in|kg)$")
    source: MeasurementSource
    confidence: float = Field(ge=0.0, le=1.0, description="1.0 for user manual, model confidence for CV")
    captured_at: datetime
    profile_version: int = Field(default=1, ge=1)


class BodyProfileV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    profile_id: str
    user_id: str
    height_cm: Optional[float] = Field(default=None, gt=0.0, lt=300.0)
    weight_kg: Optional[float] = Field(default=None, gt=0.0, lt=500.0)
    body_silhouette: Optional[str] = None
    skin_tone_hex: Optional[str] = Field(default=None, pattern="^#[0-9A-Fa-f]{6}$")
    skin_undertone: Optional[str] = None
    is_active: bool = True
    created_at: datetime


class TopFitPreference(str, Enum):
    SLIM = "slim"
    REGULAR = "regular"
    RELAXED = "relaxed"
    OVERSIZED = "oversized"


class BottomFitPreference(str, Enum):
    SKINNY = "skinny"
    SLIM = "slim"
    STRAIGHT = "straight"
    RELAXED = "relaxed"
    WIDE_LEG = "wide_leg"


class FitProfileV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    user_id: str
    preferred_top_fit: TopFitPreference = TopFitPreference.RELAXED
    preferred_bottom_fit: BottomFitPreference = BottomFitPreference.STRAIGHT
    known_best_sizes: Dict[str, str] = Field(
        default_factory=dict,
        description="e.g. {'Zara': 'L', 'Uniqlo': 'M'}",
    )
    latest_measurements: Dict[str, MeasurementV1] = Field(default_factory=dict)
    fit_bias_tolerances: Dict[str, float] = Field(
        default_factory=dict,
        description="Calibration offsets: e.g. {'chest_ease_cm': 4.0}",
    )
    updated_at: datetime


class DerivedProfileV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    user_id: str
    silhouette_type: Optional[str] = None
    skin_undertone: Optional[str] = None
    style_affinities: List[str] = Field(default_factory=list)
    preferred_fits: Dict[str, str] = Field(default_factory=dict)
    standard_sizes: Dict[str, str] = Field(default_factory=dict)
    color_palette_affinity: List[str] = Field(default_factory=list)
