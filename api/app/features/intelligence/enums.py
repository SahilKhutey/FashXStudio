from enum import StrEnum


class IntelligenceType(StrEnum):
    PRODUCT_ANALYSIS = "product_analysis"
    OUTFIT_ANALYSIS = "outfit_analysis"
    STYLE_ANALYSIS = "style_analysis"
    COMPATIBILITY = "compatibility"
    RECOMMENDATION = "recommendation"
    ALTERNATIVE = "alternative"


class IntelligenceStatus(StrEnum):
    REQUESTED = "requested"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IntelligenceState(StrEnum):
    IDLE = "idle"
    LOADING = "loading"
    ANALYZING = "analyzing"
    READY = "ready"
    EMPTY = "empty"
    ERROR = "error"
