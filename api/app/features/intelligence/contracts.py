from dataclasses import dataclass

from .enums import IntelligenceType


@dataclass(frozen=True)
class IntelligenceRequest:
    user_id: str | None
    target_id: str
    intelligence_type: IntelligenceType
    region: str | None = None
