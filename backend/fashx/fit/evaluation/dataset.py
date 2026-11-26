"""Manually labelled fit evaluation dataset schema and split-leakage validation (Task 8.3.10)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from fashx.fit.enums import EvaluationLabel, EvaluationSplit, MeasurementBasis


class EvaluationDatasetError(ValueError):
    """Raised when an evaluation dataset fails provenance, label, or split isolation checks."""


@dataclass(frozen=True)
class EvaluationDatasetCase:
    """Single manually labelled evaluation case with immutable provenance."""

    case_id: str
    dataset_version: str
    split: EvaluationSplit
    shopper_key: str
    merchant_id: str
    product_id: str
    merchant_offer_id: str
    category: str
    variant_id: str | None
    size_chart_revision: int
    measurement_basis: MeasurementBasis
    expected_label: EvaluationLabel
    expected_size: str | None
    acceptable_sizes: tuple[str, ...]
    reviewer_id: str
    labelled_at: datetime
    evidence_reference: str
    is_synthetic: bool = False


def validate_dataset_splits(cases: list[EvaluationDatasetCase]) -> None:
    """Enforce zero empty datasets, valid provenance, and zero shopper/product split leakage."""
    if not cases:
        raise EvaluationDatasetError("Evaluation dataset is empty.")

    shopper_splits: dict[str, set[EvaluationSplit]] = {}
    product_splits: dict[str, set[EvaluationSplit]] = {}

    for case in cases:
        if not case.reviewer_id.strip():
            raise EvaluationDatasetError(f"Case '{case.case_id}' missing human reviewer_id.")
        if not case.evidence_reference.strip():
            raise EvaluationDatasetError(f"Case '{case.case_id}' missing evidence_reference.")
        if case.labelled_at.tzinfo is None:
            raise EvaluationDatasetError(f"Case '{case.case_id}' labelled_at must be timezone-aware.")
        shopper_splits.setdefault(case.shopper_key, set()).add(case.split)
        product_splits.setdefault(f"{case.merchant_id}:{case.product_id}", set()).add(case.split)

    leaked_shoppers = [k for k, splits in shopper_splits.items() if len(splits) > 1]
    if leaked_shoppers:
        raise EvaluationDatasetError(
            f"Shopper leakage detected across splits for keys: {sorted(leaked_shoppers)[:5]}"
        )
    leaked_products = [k for k, splits in product_splits.items() if len(splits) > 1]
    if leaked_products:
        raise EvaluationDatasetError(
            f"Product leakage detected across splits for keys: {sorted(leaked_products)[:5]}"
        )


def load_dataset_json(path: str | Path) -> list[EvaluationDatasetCase]:
    """Load and validate a versioned JSON evaluation dataset from disk."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    version = str(raw.get("dataset_version", "unknown"))
    records = raw.get("cases")
    if not isinstance(records, list) or not records:
        raise EvaluationDatasetError("Dataset JSON must contain a non-empty 'cases' list.")

    parsed: list[EvaluationDatasetCase] = []
    for item in records:
        parsed_dt = datetime.fromisoformat(str(item["labelled_at"]))
        if parsed_dt.tzinfo is None:
            parsed_dt = parsed_dt.replace(tzinfo=UTC)
        parsed.append(
            EvaluationDatasetCase(
                case_id=str(item["case_id"]),
                dataset_version=str(item.get("dataset_version", version)),
                split=EvaluationSplit(str(item["split"]).upper()),
                shopper_key=str(item["shopper_key"]),
                merchant_id=str(item["merchant_id"]),
                product_id=str(item["product_id"]),
                merchant_offer_id=str(item["merchant_offer_id"]),
                category=str(item["category"]).upper(),
                variant_id=item.get("variant_id"),
                size_chart_revision=int(item["size_chart_revision"]),
                measurement_basis=MeasurementBasis(str(item["measurement_basis"]).upper()),
                expected_label=EvaluationLabel(str(item["expected_label"]).upper()),
                expected_size=item.get("expected_size"),
                acceptable_sizes=tuple(item.get("acceptable_sizes") or ()),
                reviewer_id=str(item["reviewer_id"]),
                labelled_at=parsed_dt,
                evidence_reference=str(item["evidence_reference"]),
                is_synthetic=bool(item.get("is_synthetic", False)),
            )
        )
    validate_dataset_splits(parsed)
    return parsed
