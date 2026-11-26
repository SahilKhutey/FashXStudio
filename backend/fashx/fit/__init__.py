"""Fit recommendation domain package (Phase 07.8 compatibility + Phase 08.3 engine)."""

from fashx.fit.contracts import (
    EvidenceReference,
    FitFeedbackCreateRequest,
    FitFeedbackResponse,
    FitModelSpec,
    FitOutcome,
    FitProductInput,
    FitRecommendationRequest,
    FitRecommendationResponse,
    FitRecommendationResult,
    MeasurementValue,
    MerchantSizeOption,
    SizeRange,
)
from fashx.fit.enums import (
    FitFeedbackReason,
    FitPreference,
    FitReasonCode,
    MeasurementBasis,
    MissingDataCode,
    RecommendationStatus,
)
from fashx.fit.service import (
    FitEvidenceSecurityError,
    FitRecommendationService,
)

__all__ = [
    "EvidenceReference",
    "FitEvidenceSecurityError",
    "FitFeedbackCreateRequest",
    "FitFeedbackReason",
    "FitFeedbackResponse",
    "FitModelSpec",
    "FitOutcome",
    "FitPreference",
    "FitProductInput",
    "FitReasonCode",
    "FitRecommendationRequest",
    "FitRecommendationResponse",
    "FitRecommendationResult",
    "FitRecommendationService",
    "MeasurementBasis",
    "MeasurementValue",
    "MerchantSizeOption",
    "MissingDataCode",
    "RecommendationStatus",
    "SizeRange",
]
