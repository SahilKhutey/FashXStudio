"""
Feedback Domain Contracts v1
Strict separation of Taste/Preference Feedback from Physical Sizing Ground Truth.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import Field
from schemas.base import BaseContractModel


class PreferenceAction(str, Enum):
    LIKE = "like"
    REJECT = "reject"
    SAVE_TO_CLOSET = "save_to_closet"
    TRY_ON = "try_on"
    BUY_CLICK = "buy_click"


class PreferenceFeedbackV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    feedback_id: str
    user_id: str
    canonical_garment_id: str
    action: PreferenceAction
    rejection_tags: Optional[List[str]] = Field(
        default=None,
        description="e.g. ['color_mismatch', 'too_loose', 'price_too_high']",
    )
    feed_context: Optional[str] = Field(
        default="home_feed",
        description="e.g. 'home_feed', 'trending', 'closet_builder'",
    )
    session_id: str
    timestamp: datetime


class FitOutcome(str, Enum):
    WAY_TOO_TIGHT = "way_too_tight"
    SLIGHTLY_TIGHT = "slightly_tight"
    TRUE_TO_SIZE = "true_to_size"
    SLIGHTLY_LOOSE = "slightly_loose"
    WAY_TOO_LOOSE = "way_too_loose"


class Disposition(str, Enum):
    KEPT = "kept"
    RETURNED_WRONG_SIZE = "returned_wrong_size"
    RETURNED_POOR_QUALITY = "returned_poor_quality"
    RETURNED_STYLE_MISMATCH = "returned_style_mismatch"


class FitFeedbackV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    feedback_id: str
    user_id: str
    brand: str
    category: str
    fit_type: str = Field(description="e.g. 'relaxed', 'slim', 'oversized'")
    canonical_garment_id: str
    variant_id: str
    purchased_size: str
    overall_fit: FitOutcome
    chest_fit: Optional[FitOutcome] = None
    waist_fit: Optional[FitOutcome] = None
    length_fit: Optional[FitOutcome] = None
    shoulder_fit: Optional[FitOutcome] = None
    disposition: Disposition
    notes: Optional[str] = None
    timestamp: datetime
