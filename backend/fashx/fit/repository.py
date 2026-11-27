"""Repository for Phase 08.3 fit recommendation snapshots, evidence, candidates, feedback, and evaluation."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.commerce_feedback import FitFeedback
from database.models.fit import (
    FitEvaluationRunRecord,
    FitRecommendationCandidateRecord,
    FitRecommendationEvidenceRecord,
)
from database.models.tryon import FitRecommendation
from fashx.fit.evaluation.report import EvaluationReport


def _as_uuid(value: UUID | str | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


class DuplicateFitFeedbackError(ValueError):
    """Raised when a shopper submits duplicate feedback for the same recommendation."""


class FitRecommendationRepository:
    """Dual SQLAlchemy + in-memory repository for recommendation reproducibility and feedback."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session
        self._mem_recommendations: dict[str, FitRecommendation] = {}
        self._mem_evidence: dict[str, list[FitRecommendationEvidenceRecord]] = {}
        self._mem_candidates: dict[str, list[FitRecommendationCandidateRecord]] = {}
        self._mem_feedback: dict[str, FitFeedback] = {}
        self._mem_eval_runs: list[FitEvaluationRunRecord] = []

    async def save_recommendation_snapshot(
        self,
        *,
        recommendation_id: UUID | str,
        user_id: UUID | str,
        product_id: UUID | str,
        merchant_id: UUID | str | None,
        merchant_product_id: UUID | str | None,
        merchant_offer_id: UUID | str | None,
        variant_id: str | None,
        size_chart_id: UUID | str | None,
        size_chart_revision: int | None,
        shopper_measurement_revision: int | None,
        category_policy_version: str | None,
        fit_algorithm_version: str,
        fit_preference_revision: int | None,
        source_permission_revision: int | None,
        status: str,
        recommended_size: str | None,
        alternative_sizes: list[str],
        reason_codes: list[str],
        internal_confidence_score: Decimal,
        evidence_records: list[dict[str, Any]],
        candidate_records: list[dict[str, Any]],
        expires_at: datetime | None = None,
    ) -> FitRecommendation:
        rec_uuid = _as_uuid(recommendation_id) or uuid4()
        now = datetime.now(UTC)

        rec = FitRecommendation(
            id=rec_uuid,
            user_id=_as_uuid(user_id) or uuid4(),
            product_id=_as_uuid(product_id) or uuid4(),
            merchant_id=_as_uuid(merchant_id),
            merchant_product_id=_as_uuid(merchant_product_id),
            merchant_offer_id=_as_uuid(merchant_offer_id),
            variant_id=variant_id,
            size_chart_id=_as_uuid(size_chart_id),
            size_chart_revision=size_chart_revision,
            shopper_measurement_revision=shopper_measurement_revision,
            category_policy_version=category_policy_version,
            fit_algorithm_version=fit_algorithm_version,
            fit_preference_revision=fit_preference_revision,
            source_permission_revision=source_permission_revision,
            outcome=status[:40],
            recommendation_status=status,
            recommended_size=recommended_size,
            alternative_sizes=alternative_sizes,
            explanation_code=reason_codes[0] if reason_codes else status,
            reason_codes_json=reason_codes,
            evidence_json=evidence_records,
            fit_model_version=fit_algorithm_version,
            internal_confidence_score=internal_confidence_score,
            is_valid=True,
            expires_at=expires_at,
            created_at=now,
        )

        # Retain non-UUID caller metadata on in-memory records when DB is absent
        rec._raw_rec_id = str(recommendation_id)  # type: ignore[attr-defined]
        rec._raw_user_id = str(user_id)  # type: ignore[attr-defined]
        rec._raw_product_id = str(product_id)  # type: ignore[attr-defined]
        rec._raw_merchant_id = str(merchant_id) if merchant_id else None  # type: ignore[attr-defined]
        rec._raw_chart_id = str(size_chart_id) if size_chart_id else None  # type: ignore[attr-defined]
        rec._raw_offer_id = str(merchant_offer_id) if merchant_offer_id else None  # type: ignore[attr-defined]

        ev_rows = [
            FitRecommendationEvidenceRecord(
                id=uuid4(),
                recommendation_id=rec_uuid,
                source_type=str(item["source_type"]),
                source_id=str(item["source_id"]),
                source_revision=str(item["source_revision"]),
                measurement_basis=item.get("measurement_basis"),
                evidence_status=str(item.get("evidence_status", "VERIFIED")),
                metadata_json=item.get("metadata"),
                created_at=now,
            )
            for item in evidence_records
        ]
        cand_rows = [
            FitRecommendationCandidateRecord(
                id=uuid4(),
                recommendation_id=rec_uuid,
                variant_id=str(item["variant_id"]),
                merchant_size_label=str(item["merchant_size_label"]),
                is_available=bool(item.get("is_available", True)),
                matched=bool(item.get("matched", False)),
                mismatched_fields_json=list(item.get("mismatched_fields") or []),
                rank_order=int(item.get("rank_order", 0)),
                created_at=now,
            )
            for item in candidate_records
        ]

        if self._session is not None:
            self._session.add(rec)
            await self._session.flush()
            for row in ev_rows:
                self._session.add(row)
            for crow in cand_rows:
                self._session.add(crow)
            await self._session.flush()
            return rec

        key = str(recommendation_id)
        self._mem_recommendations[key] = rec
        self._mem_evidence[key] = ev_rows
        self._mem_candidates[key] = cand_rows
        return rec

    async def get_recommendation(self, recommendation_id: UUID | str) -> FitRecommendation | None:
        if self._session is not None:
            uid = _as_uuid(recommendation_id)
            if uid is None:
                return None
            stmt = select(FitRecommendation).where(FitRecommendation.id == uid)
            res = await self._session.execute(stmt)
            return res.scalar_one_or_none()
        return self._mem_recommendations.get(str(recommendation_id))

    async def get_recommendation_for_owner(
        self, recommendation_id: UUID | str, shopper_id: UUID | str
    ) -> FitRecommendation:
        rec = await self.get_recommendation(recommendation_id)
        if rec is None:
            raise KeyError(f"Recommendation '{recommendation_id}' not found.")
        raw_owner = getattr(rec, "_raw_user_id", str(rec.user_id))
        if str(rec.user_id) != str(shopper_id) and raw_owner != str(shopper_id):
            raise PermissionError("Access denied for recommendation owned by another shopper.")
        return rec

    async def invalidate_for_chart(
        self, size_chart_id: UUID | str, *, reason: str = "SIZE_CHART_CHANGED"
    ) -> int:
        now = datetime.now(UTC)
        if self._session is not None:
            uid = _as_uuid(size_chart_id)
            if uid is None:
                return 0
            stmt = (
                update(FitRecommendation)
                .where(FitRecommendation.size_chart_id == uid, FitRecommendation.is_valid.is_(True))
                .values(is_valid=False, invalidation_reason=reason, invalidated_at=now)
            )
            res = await self._session.execute(stmt)
            return int(getattr(res, "rowcount", 0) or 0)

        count = 0
        for rec in self._mem_recommendations.values():
            raw_cid = getattr(rec, "_raw_chart_id", str(rec.size_chart_id or ""))
            if rec.is_valid and (raw_cid == str(size_chart_id) or str(rec.size_chart_id) == str(size_chart_id)):
                rec.is_valid = False
                rec.invalidation_reason = reason
                rec.invalidated_at = now
                count += 1
        return count

    async def invalidate_for_product(
        self, product_id: UUID | str, *, reason: str = "PRODUCT_UPDATED"
    ) -> int:
        now = datetime.now(UTC)
        if self._session is not None:
            uid = _as_uuid(product_id)
            if uid is None:
                return 0
            stmt = (
                update(FitRecommendation)
                .where(FitRecommendation.product_id == uid, FitRecommendation.is_valid.is_(True))
                .values(is_valid=False, invalidation_reason=reason, invalidated_at=now)
            )
            res = await self._session.execute(stmt)
            return int(getattr(res, "rowcount", 0) or 0)

        count = 0
        for rec in self._mem_recommendations.values():
            raw_pid = getattr(rec, "_raw_product_id", str(rec.product_id))
            if rec.is_valid and (raw_pid == str(product_id) or str(rec.product_id) == str(product_id)):
                rec.is_valid = False
                rec.invalidation_reason = reason
                rec.invalidated_at = now
                count += 1
        return count

    async def invalidate_for_user(
        self, user_id: UUID | str, *, reason: str = "SHOPPER_PROFILE_CHANGED"
    ) -> int:
        now = datetime.now(UTC)
        if self._session is not None:
            uid = _as_uuid(user_id)
            if uid is None:
                return 0
            stmt = (
                update(FitRecommendation)
                .where(FitRecommendation.user_id == uid, FitRecommendation.is_valid.is_(True))
                .values(is_valid=False, invalidation_reason=reason, invalidated_at=now)
            )
            res = await self._session.execute(stmt)
            return int(getattr(res, "rowcount", 0) or 0)

        count = 0
        for rec in self._mem_recommendations.values():
            raw_uid = getattr(rec, "_raw_user_id", str(rec.user_id))
            if rec.is_valid and (raw_uid == str(user_id) or str(rec.user_id) == str(user_id)):
                rec.is_valid = False
                rec.invalidation_reason = reason
                rec.invalidated_at = now
                count += 1
        return count

    async def get_feedback_for_recommendation(
        self, recommendation_id: UUID | str, shopper_id: UUID | str
    ) -> FitFeedback | None:
        if self._session is not None:
            rec_uid = _as_uuid(recommendation_id)
            user_uid = _as_uuid(shopper_id)
            if rec_uid is None or user_uid is None:
                return None
            stmt = select(FitFeedback).where(
                FitFeedback.recommendation_id == rec_uid,
                FitFeedback.user_id == user_uid,
                FitFeedback.deleted_at.is_(None),
            )
            res = await self._session.execute(stmt)
            return res.scalar_one_or_none()

        for fb in self._mem_feedback.values():
            if (
                getattr(fb, "_raw_rec_id", str(fb.recommendation_id)) == str(recommendation_id)
                and getattr(fb, "_raw_user_id", str(fb.user_id)) == str(shopper_id)
                and fb.deleted_at is None
            ):
                return fb
        return None

    async def save_feedback(
        self,
        *,
        recommendation: FitRecommendation,
        shopper_id: UUID | str,
        reason: str,
        purchase_status: str,
        tried_on: bool,
        kept_item: bool | None,
        selected_different_size: bool,
        feedback_basis: str,
        review_status: str,
        comment: str | None,
        category: str = "UNKNOWN",
    ) -> FitFeedback:
        rec_key = getattr(recommendation, "_raw_rec_id", str(recommendation.id))
        existing = await self.get_feedback_for_recommendation(rec_key, shopper_id)
        if existing is not None:
            raise DuplicateFitFeedbackError(
                f"Feedback already submitted for recommendation '{rec_key}'."
            )

        now = datetime.now(UTC)
        fb = FitFeedback(
            id=uuid4(),
            user_id=_as_uuid(shopper_id) or recommendation.user_id,
            garment_id=recommendation.product_id,
            brand_id=None,
            recommendation_id=recommendation.id,
            merchant_id=recommendation.merchant_id,
            merchant_offer_id=recommendation.merchant_offer_id,
            size_chart_id=recommendation.size_chart_id,
            size_chart_revision=recommendation.size_chart_revision,
            category=category,
            fit_type=None,
            size_label=recommendation.recommended_size or "ABSTAINED",
            verdict=reason,
            reason=reason,
            purchase_status=purchase_status,
            tried_on=tried_on,
            kept_item=kept_item,
            selected_different_size=selected_different_size,
            feedback_basis=feedback_basis,
            comment=comment,
            review_status=review_status,
            created_at=now,
        )
        fb._raw_rec_id = rec_key  # type: ignore[attr-defined]
        fb._raw_user_id = str(shopper_id)  # type: ignore[attr-defined]
        fb._raw_product_id = getattr(recommendation, "_raw_product_id", str(recommendation.product_id))  # type: ignore[attr-defined]
        fb._raw_merchant_id = getattr(recommendation, "_raw_merchant_id", str(recommendation.merchant_id) if recommendation.merchant_id else None)  # type: ignore[attr-defined]
        fb._raw_chart_id = getattr(recommendation, "_raw_chart_id", str(recommendation.size_chart_id) if recommendation.size_chart_id else None)  # type: ignore[attr-defined]

        if self._session is not None:
            self._session.add(fb)
            await self._session.flush()
            return fb

        self._mem_feedback[str(fb.id)] = fb
        return fb

    async def review_feedback(
        self, feedback_id: UUID | str, *, review_status: str
    ) -> FitFeedback:
        now = datetime.now(UTC)
        if self._session is not None:
            uid = _as_uuid(feedback_id)
            if uid is None:
                raise KeyError(f"Feedback '{feedback_id}' not found.")
            fb = await self._session.get(FitFeedback, uid)
            if fb is None:
                raise KeyError(f"Feedback '{feedback_id}' not found.")
            fb.review_status = review_status
            fb.reviewed_at = now
            await self._session.flush()
            return fb

        fb = self._mem_feedback.get(str(feedback_id))
        if fb is None:
            raise KeyError(f"Feedback '{feedback_id}' not found.")
        fb.review_status = review_status
        fb.reviewed_at = now
        return fb

    async def delete_feedback(self, feedback_id: UUID | str, shopper_id: UUID | str) -> bool:
        now = datetime.now(UTC)
        if self._session is not None:
            uid = _as_uuid(feedback_id)
            if uid is None:
                raise KeyError(f"Feedback '{feedback_id}' not found.")
            fb = await self._session.get(FitFeedback, uid)
            if fb is None or fb.deleted_at is not None:
                raise KeyError(f"Feedback '{feedback_id}' not found.")
            if str(fb.user_id) != str(shopper_id):
                raise PermissionError("Cannot delete feedback belonging to another shopper.")
            fb.deleted_at = now
            fb.comment = None
            await self._session.flush()
            return True

        fb = self._mem_feedback.get(str(feedback_id))
        if fb is None or fb.deleted_at is not None:
            raise KeyError(f"Feedback '{feedback_id}' not found.")
        if getattr(fb, "_raw_user_id", str(fb.user_id)) != str(shopper_id):
            raise PermissionError("Cannot delete feedback belonging to another shopper.")
        fb.deleted_at = now
        fb.comment = None
        return True

    async def save_evaluation_run(self, report: EvaluationReport) -> FitEvaluationRunRecord:
        metrics = report.metrics
        exact = metrics.get("exact_size_accuracy")
        acc = metrics.get("acceptable_size_accuracy")
        false_r = metrics.get("false_recommendation_rate")

        def _dec(val: object) -> Decimal | None:
            return Decimal(str(val)) if isinstance(val, int | float | Decimal) else None

        rec = FitEvaluationRunRecord(
            id=uuid4(),
            dataset_version=report.dataset_version,
            fit_algorithm_version=report.fit_algorithm_version,
            category_policy_version=report.category_policy_version,
            total_cases=int(metrics.get("total_cases", 0)),  # type: ignore[arg-type]
            recommended_count=int(metrics.get("recommendations_made", 0)),  # type: ignore[arg-type]
            abstention_count=int(metrics.get("abstentions_made", 0)),  # type: ignore[arg-type]
            exact_size_accuracy=_dec(exact),
            acceptable_size_accuracy=_dec(acc),
            coverage=Decimal(str(metrics.get("coverage", 0))),
            abstention_rate=Decimal(str(metrics.get("abstention_rate", 0))),
            false_recommendation_rate=_dec(false_r),
            metrics_json={
                "total_cases": metrics.get("total_cases"),
                "coverage": metrics.get("coverage"),
                "abstention_rate": metrics.get("abstention_rate"),
                "exact_size_accuracy": metrics.get("exact_size_accuracy"),
                "acceptable_size_accuracy": metrics.get("acceptable_size_accuracy"),
                "false_recommendation_rate": metrics.get("false_recommendation_rate"),
                "small_sample_warning": metrics.get("small_sample_warning"),
            },
            gate_passed=report.all_gates_passed,
            created_at=report.generated_at,
        )
        if self._session is not None:
            self._session.add(rec)
            await self._session.flush()
            return rec
        self._mem_eval_runs.append(rec)
        return rec
