"""Evaluation framework for Phase 08.3 Fit Recommendation accuracy and calibration."""

from fashx.fit.evaluation.dataset import (
    EvaluationDatasetCase,
    EvaluationDatasetError,
    load_dataset_json,
    validate_dataset_splits,
)
from fashx.fit.evaluation.metrics import (
    CalibrationBin,
    EvaluationCase,
    GroupMetrics,
    evaluate_cases,
)
from fashx.fit.evaluation.report import (
    EvaluationReport,
    ReleaseGateCheck,
    build_evaluation_report,
)

__all__ = [
    "CalibrationBin",
    "EvaluationCase",
    "EvaluationDatasetCase",
    "EvaluationDatasetError",
    "EvaluationReport",
    "GroupMetrics",
    "ReleaseGateCheck",
    "build_evaluation_report",
    "evaluate_cases",
    "load_dataset_json",
    "validate_dataset_splits",
]
