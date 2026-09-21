from dataclasses import dataclass

from .enums import ConfidenceLevel, IntelligenceStatus, IntelligenceType


@dataclass(frozen=True)
class IntelligenceContext:
    user_id: str | None = None
    region: str | None = None
    styles: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    colors: tuple[str, ...] = ()
    occasions: tuple[str, ...] = ()
    seasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class FashionAttribute:
    name: str
    value: str
    confidence: float = 0.0


@dataclass(frozen=True)
class IntelligenceExplanation:
    reason: str
    evidence: tuple[str, ...] = ()
    confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW


@dataclass(frozen=True)
class IntelligenceResult:
    result_id: str
    request_id: str
    intelligence_type: IntelligenceType
    status: IntelligenceStatus
    attributes: tuple[FashionAttribute, ...] = ()
    explanation: IntelligenceExplanation | None = None
    model_version: str | None = None
