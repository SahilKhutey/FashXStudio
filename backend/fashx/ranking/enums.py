"""Enumerations for Phase 08.4 Personalized Product Ranking."""

from __future__ import annotations

from enum import Enum


class AvailabilityStatus(str, Enum):
    IN_STOCK = "IN_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    UNKNOWN = "UNKNOWN"
    DISCONTINUED = "DISCONTINUED"
    DELISTED = "DELISTED"
    TAKEDOWN = "TAKEDOWN"
    STALE = "STALE"


class SizeAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class FeedbackType(str, Enum):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"
    SAVE = "SAVE"
    REMOVE_SAVED = "REMOVE_SAVED"
    NOT_INTERESTED = "NOT_INTERESTED"


class PreferencePolarity(str, Enum):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"


class RankingReasonCode(str, Enum):
    CATEGORY_MATCH = "CATEGORY_MATCH"
    STYLE_MATCH = "STYLE_MATCH"
    COLOR_MATCH = "COLOR_MATCH"
    PRICE_MATCH = "PRICE_MATCH"
    SIZE_AVAILABLE = "SIZE_AVAILABLE"
    VISUAL_SIMILARITY = "VISUAL_SIMILARITY"
    FEEDBACK_MATCH = "FEEDBACK_MATCH"
    QUALITY_VALIDATED = "QUALITY_VALIDATED"


class ExperimentGroup(str, Enum):
    BASELINE = "BASELINE"
    PERSONALIZED = "PERSONALIZED"
