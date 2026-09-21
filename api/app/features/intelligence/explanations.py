from .enums import ConfidenceLevel
from .models import IntelligenceExplanation


def build_explanation(
    reason: str, evidence: tuple[str, ...], confidence: float
) -> IntelligenceExplanation:
    return IntelligenceExplanation(
        reason,
        evidence,
        confidence,
        ConfidenceLevel.HIGH
        if confidence >= 0.8
        else ConfidenceLevel.MEDIUM
        if confidence >= 0.5
        else ConfidenceLevel.LOW,
    )
