from .aggregation import (
    SOURCE_WEIGHTS,
    aggregate_observations,
)
from .entities import (
    Trend,
    TrendContext,
    TrendObservation,
    TrendSnapshot,
    utc_now,
)
from .enums import (
    SignalType,
    TrendDirection,
    TrendSource,
    TrendStatus,
    TrendType,
)
from .events import (
    TrendActivated,
    TrendCreated,
    TrendObservationCreated,
    TrendUpdated,
)
from .lifecycle import validate_trend_transition
from .provider import (
    TestTrendProvider,
    TrendDataProvider,
)
from .repository import (
    TrendObservationRepository,
    TrendRepository,
)
from .scoring import (
    direction_from_momentum,
    momentum_score,
    normalize,
    trend_strength,
)
from .service import TrendService

__all__ = [
    "SOURCE_WEIGHTS",
    "SignalType",
    "TestTrendProvider",
    "Trend",
    "TrendActivated",
    "TrendContext",
    "TrendCreated",
    "TrendDataProvider",
    "TrendDirection",
    "TrendObservation",
    "TrendObservationCreated",
    "TrendObservationRepository",
    "TrendRepository",
    "TrendService",
    "TrendSnapshot",
    "TrendSource",
    "TrendStatus",
    "TrendType",
    "TrendUpdated",
    "aggregate_observations",
    "direction_from_momentum",
    "momentum_score",
    "normalize",
    "trend_strength",
    "utc_now",
    "validate_trend_transition",
]
