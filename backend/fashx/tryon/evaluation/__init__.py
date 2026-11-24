"""Virtual Try-On Quality Evaluation Package (Phase 07.7)."""

from backend.fashx.tryon.evaluation.category_gate import (
    CategoryGateThresholds,
    CategoryMetrics,
    GateEvaluationResult,
    evaluate_category,
    get_category_rejection_message,
)
from backend.fashx.tryon.evaluation.contracts import (
    CategoryStatus,
    DatasetPartition,
    EvaluationDifficulty,
    EvaluationPair,
    EvaluationRunConfig,
    ExpectedOutcome,
    is_vto_category_allowed,
    load_manifest_pairs,
)
from backend.fashx.tryon.evaluation.image_metrics import (
    ImageMetricResult,
    compare_aligned_regions,
)
from backend.fashx.tryon.evaluation.legacy_visual import (
    ACCURACY_SCORES,
    VALID_ISSUE_TAGS,
    VALID_VISUAL_ACCURACIES,
    HumanVisualRating,
    VisualEvaluationSummary,
    summarize_visual_ratings,
)
from backend.fashx.tryon.evaluation.ratings import (
    RUBRIC_WEIGHTS,
    AggregatedItemRating,
    HumanQualityRating,
    ReviewDecision,
    aggregate_item_ratings,
)
from backend.fashx.tryon.evaluation.runner import (
    BenchmarkExecutionSummary,
    EvaluationItemResult,
    TryOnEvaluationRunner,
)

__all__ = [
    "CategoryStatus",
    "DatasetPartition",
    "EvaluationDifficulty",
    "EvaluationPair",
    "EvaluationRunConfig",
    "ExpectedOutcome",
    "is_vto_category_allowed",
    "load_manifest_pairs",
    "CategoryGateThresholds",
    "CategoryMetrics",
    "GateEvaluationResult",
    "evaluate_category",
    "get_category_rejection_message",
    "ImageMetricResult",
    "compare_aligned_regions",
    "RUBRIC_WEIGHTS",
    "AggregatedItemRating",
    "HumanQualityRating",
    "ReviewDecision",
    "aggregate_item_ratings",
    "BenchmarkExecutionSummary",
    "EvaluationItemResult",
    "TryOnEvaluationRunner",
    "ACCURACY_SCORES",
    "VALID_ISSUE_TAGS",
    "VALID_VISUAL_ACCURACIES",
    "HumanVisualRating",
    "VisualEvaluationSummary",
    "summarize_visual_ratings",
]
