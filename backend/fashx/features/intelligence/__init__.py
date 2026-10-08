"""F08 explainable fashion intelligence orchestration."""

from .contracts import IntelligenceRequest
from .service import FashionIntelligenceService

__all__ = ["FashionIntelligenceService", "IntelligenceRequest"]
