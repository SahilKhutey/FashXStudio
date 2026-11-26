from __future__ import annotations

import html
import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeedbackReason(str, Enum):
    """Structured shopper complaint reason codes for virtual try-on outputs."""

    GARMENT_LOOKS_DIFFERENT = "GARMENT_LOOKS_DIFFERENT"
    COLOUR_OR_PATTERN_CHANGED = "COLOUR_OR_PATTERN_CHANGED"
    GARMENT_LENGTH_OR_SHAPE = "GARMENT_LENGTH_OR_SHAPE"
    BODY_ALIGNMENT_ISSUE = "BODY_ALIGNMENT_ISSUE"
    FACE_OR_BODY_CHANGED = "FACE_OR_BODY_CHANGED"
    MISLEADING_FIT_IMPRESSION = "MISLEADING_FIT_IMPRESSION"
    LAYERING_ERROR = "LAYERING_ERROR"
    IMAGE_ARTIFACT = "IMAGE_ARTIFACT"
    OTHER = "OTHER"


class FeedbackReviewStatus(str, Enum):
    """Audit investigation and resolution states for try-on complaints."""

    RECEIVED = "RECEIVED"
    TRIAGE = "TRIAGE"
    NEEDS_MORE_INFORMATION = "NEEDS_MORE_INFORMATION"
    CONFIRMED = "CONFIRMED"
    NOT_CONFIRMED = "NOT_CONFIRMED"
    DUPLICATE = "DUPLICATE"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class FeedbackRootCause(str, Enum):
    """Categorized technical root cause of an confirmed generation defect."""

    INPUT_QUALITY = "INPUT_QUALITY"
    GARMENT_ASSET_QUALITY = "GARMENT_ASSET_QUALITY"
    GARMENT_PRESERVATION = "GARMENT_PRESERVATION"
    BODY_ALIGNMENT = "BODY_ALIGNMENT"
    IDENTITY_PRESERVATION = "IDENTITY_PRESERVATION"
    LAYERING = "LAYERING"
    CATEGORY_MISMATCH = "CATEGORY_MISMATCH"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    PRODUCT_DATA_ISSUE = "PRODUCT_DATA_ISSUE"
    PRESENTATION_MISLEADING = "PRESENTATION_MISLEADING"
    UNDETERMINED = "UNDETERMINED"


class FeedbackSeverity(str, Enum):
    """Defect impact severity governing evaluation regression tracking and category blocks."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TryOnFeedbackRequest(BaseModel):
    """Request payload to report an inaccurate or misleading try-on result."""

    model_config = ConfigDict(extra="forbid")

    reason_code: FeedbackReason
    details: str | None = Field(default=None, max_length=2000)
    include_in_quality_review: bool = Field(
        default=False,
        description=(
            "Whether shopper explicitly authorizes restricted internal review of the generated image. "
            "Does NOT authorize model training."
        ),
    )

    @field_validator("details")
    @classmethod
    def sanitize_details(cls, v: str | None) -> str | None:
        if v is None:
            return None
        # Strip potential script or HTML tags and escape
        clean = re.sub(r"<[^>]+>", "", v)
        clean = html.escape(clean.strip())
        return clean if clean else None


class TryOnFeedbackResponse(BaseModel):
    """Submission receipt returned to the reporting shopper."""

    model_config = ConfigDict(extra="forbid")

    feedback_id: str
    job_id: str
    user_id: str
    reason_code: FeedbackReason
    status: FeedbackReviewStatus = FeedbackReviewStatus.RECEIVED
    include_in_quality_review: bool
    message: str = "Your feedback has been recorded."
    created_at: datetime


class TryOnFeedbackReviewAction(BaseModel):
    """Internal review investigation decision and classification."""

    model_config = ConfigDict(extra="forbid")

    reviewer_id: str
    review_status: FeedbackReviewStatus
    root_cause: FeedbackRootCause | None = None
    severity: FeedbackSeverity | None = None
    resolution_notes: str | None = Field(default=None, max_length=2000)
    linked_evaluation_item_id: str | None = None
    category_action_required: bool = False
