"""Persistence repositories for Phase 08.4 preferences, feedback, and events."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.ranking import (
    ProductFeedbackRecord,
    RankingEventRecord,
    RankingPreferenceRecord,
)
from fashx.ranking.contracts import (
    ProductFeedbackResponse,
    RankingCandidate,
    RankingContext,
    ShopperPreferenceSnapshot,
    ShopperRankingPreferencesResponse,
    ShopperRankingPreferencesUpdate,
    StylePreferenceEntry,
)
from fashx.ranking.enums import FeedbackType, PreferencePolarity


class RankingCandidateSource(Protocol):
    """Candidate retrieval interface consumed by PersonalizedRankingService."""

    def retrieve(self, context: RankingContext) -> list[RankingCandidate]: ...


class InMemoryRankingStore:
    """In-memory store supporting deterministic unit and API tests."""

    def __init__(self, candidates: list[RankingCandidate] | None = None) -> None:
        self.candidates: list[RankingCandidate] = list(candidates or [])
        self.preferences: dict[str, ShopperRankingPreferencesResponse] = {}
        self.feedback: dict[str, dict[str, list[ProductFeedbackResponse]]] = {}
        self.events: list[dict[str, object]] = []

    def retrieve(self, context: RankingContext) -> list[RankingCandidate]:
        return list(self.candidates)

    def get_preferences(self, shopper_id: str) -> ShopperRankingPreferencesResponse:
        return self.preferences.get(
            shopper_id,
            ShopperRankingPreferencesResponse(
                style_preferences=[],
                preferred_colors=[],
                disliked_colors=[],
                preferred_categories=[],
                budget_min=None,
                budget_max=None,
                currency="INR",
                revision=1,
            ),
        )

    def update_preferences(
        self, shopper_id: str, patch: ShopperRankingPreferencesUpdate
    ) -> ShopperRankingPreferencesResponse:
        current = self.get_preferences(shopper_id)
        updated = ShopperRankingPreferencesResponse(
            style_preferences=(
                patch.style_preferences
                if patch.style_preferences is not None
                else current.style_preferences
            ),
            preferred_colors=(
                [c.strip().upper() for c in patch.preferred_colors if c.strip()]
                if patch.preferred_colors is not None
                else current.preferred_colors
            ),
            disliked_colors=(
                [c.strip().upper() for c in patch.disliked_colors if c.strip()]
                if patch.disliked_colors is not None
                else current.disliked_colors
            ),
            preferred_categories=(
                [c.strip().upper() for c in patch.preferred_categories if c.strip()]
                if patch.preferred_categories is not None
                else current.preferred_categories
            ),
            budget_min=patch.budget_min if patch.budget_min is not None else current.budget_min,
            budget_max=patch.budget_max if patch.budget_max is not None else current.budget_max,
            currency=(patch.currency.upper() if patch.currency else current.currency),
            revision=current.revision + 1,
        )
        self.preferences[shopper_id] = updated
        return updated

    def submit_feedback(
        self, shopper_id: str, product_id: str, feedback_type: FeedbackType
    ) -> ProductFeedbackResponse:
        user_fb = self.feedback.setdefault(shopper_id, {})
        items = user_fb.setdefault(product_id, [])
        # Deactivate prior conflicting entries when updating state
        rec = ProductFeedbackResponse(
            product_id=product_id,
            feedback_type=feedback_type,
            is_active=True,
            created_at=datetime.now(UTC),
        )
        items.append(rec)
        return rec

    def get_feedback(self, shopper_id: str, product_id: str) -> list[ProductFeedbackResponse]:
        return [
            item
            for item in self.feedback.get(shopper_id, {}).get(product_id, [])
            if item.is_active
        ]

    def delete_feedback(self, shopper_id: str, product_id: str) -> int:
        items = self.feedback.get(shopper_id, {}).get(product_id, [])
        count = sum(1 for item in items if item.is_active)
        self.feedback.get(shopper_id, {})[product_id] = []
        return count

    def build_shopper_snapshot(self, shopper_id: str) -> ShopperPreferenceSnapshot:
        pref = self.get_preferences(shopper_id)
        liked: dict[str, float] = {}
        disliked: dict[str, float] = {}
        for entry in pref.style_preferences:
            if entry.preference == PreferencePolarity.LIKE:
                liked[entry.style_id.upper()] = entry.strength
            else:
                disliked[entry.style_id.upper()] = entry.strength
        fb_map: dict[str, list[str]] = {}
        for pid, records in self.feedback.get(shopper_id, {}).items():
            active = [r.feedback_type.value for r in records if r.is_active]
            if active:
                fb_map[pid] = active
        return ShopperPreferenceSnapshot(
            shopper_id=shopper_id,
            profile_revision=pref.revision,
            liked_styles=liked,
            disliked_styles=disliked,
            preferred_colors=frozenset(pref.preferred_colors),
            disliked_colors=frozenset(pref.disliked_colors),
            preferred_categories=frozenset(pref.preferred_categories),
            budget_min=pref.budget_min,
            budget_max=pref.budget_max,
            currency=pref.currency,
            feedback_by_product=fb_map,
        )


class SqlRankingRepository:
    """Async SQLAlchemy repository for ranking preferences, feedback, and audit events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_preferences(self, user_id: UUID) -> ShopperRankingPreferencesResponse:
        stmt = select(RankingPreferenceRecord).where(RankingPreferenceRecord.user_id == user_id)
        rec = (await self._session.execute(stmt)).scalar_one_or_none()
        if rec is None:
            return ShopperRankingPreferencesResponse(
                style_preferences=[],
                preferred_colors=[],
                disliked_colors=[],
                preferred_categories=[],
                budget_min=None,
                budget_max=None,
                currency="INR",
                revision=1,
            )
        styles = [
            StylePreferenceEntry(
                style_id=str(item["style_id"]),
                preference=PreferencePolarity(str(item["preference"])),
                strength=float(item.get("strength", 1.0)),  # type: ignore[arg-type]
            )
            for item in rec.style_preferences_json
        ]
        return ShopperRankingPreferencesResponse(
            style_preferences=styles,
            preferred_colors=list(rec.preferred_colors_json),
            disliked_colors=list(rec.disliked_colors_json),
            preferred_categories=list(rec.preferred_categories_json),
            budget_min=rec.budget_min,
            budget_max=rec.budget_max,
            currency=rec.currency,
            revision=rec.revision,
        )

    async def upsert_preferences(
        self, user_id: UUID, patch: ShopperRankingPreferencesUpdate
    ) -> ShopperRankingPreferencesResponse:
        stmt = select(RankingPreferenceRecord).where(RankingPreferenceRecord.user_id == user_id)
        rec = (await self._session.execute(stmt)).scalar_one_or_none()
        if rec is None:
            rec = RankingPreferenceRecord(
                user_id=user_id,
                style_preferences_json=[],
                preferred_colors_json=[],
                disliked_colors_json=[],
                preferred_categories_json=[],
                budget_min=Decimal(patch.budget_min) if patch.budget_min is not None else None,
                budget_max=Decimal(patch.budget_max) if patch.budget_max is not None else None,
                currency=(patch.currency.upper() if patch.currency else "INR"),
                revision=1,
            )
            self._session.add(rec)
        else:
            rec.revision += 1

        if patch.style_preferences is not None:
            rec.style_preferences_json = [
                {
                    "style_id": s.style_id.strip().upper(),
                    "preference": s.preference.value,
                    "strength": s.strength,
                }
                for s in patch.style_preferences
            ]
        if patch.preferred_colors is not None:
            rec.preferred_colors_json = [c.strip().upper() for c in patch.preferred_colors if c.strip()]
        if patch.disliked_colors is not None:
            rec.disliked_colors_json = [c.strip().upper() for c in patch.disliked_colors if c.strip()]
        if patch.preferred_categories is not None:
            rec.preferred_categories_json = [
                c.strip().upper() for c in patch.preferred_categories if c.strip()
            ]
        if patch.budget_min is not None:
            rec.budget_min = patch.budget_min
        if patch.budget_max is not None:
            rec.budget_max = patch.budget_max
        if patch.currency is not None:
            rec.currency = patch.currency.upper()

        await self._session.flush()
        return await self.get_preferences(user_id)

    async def submit_feedback(
        self,
        user_id: UUID,
        product_id: str,
        feedback_type: FeedbackType,
        source: str = "api",
    ) -> ProductFeedbackResponse:
        stmt = select(ProductFeedbackRecord).where(
            ProductFeedbackRecord.user_id == user_id,
            ProductFeedbackRecord.product_id == product_id,
            ProductFeedbackRecord.feedback_type == feedback_type.value,
        )
        rec = (await self._session.execute(stmt)).scalar_one_or_none()
        if rec is None:
            rec = ProductFeedbackRecord(
                user_id=user_id,
                product_id=product_id,
                feedback_type=feedback_type.value,
                source=source,
                is_active=True,
            )
            self._session.add(rec)
        else:
            rec.is_active = True
            rec.deleted_at = None
            rec.source = source
        await self._session.flush()
        return ProductFeedbackResponse(
            product_id=rec.product_id,
            feedback_type=FeedbackType(rec.feedback_type),
            is_active=rec.is_active,
            created_at=rec.created_at or datetime.now(UTC),
        )

    async def record_event(
        self,
        *,
        request_id: str,
        user_id: UUID,
        ranking_version: str,
        config_version: str,
        taxonomy_version: str,
        candidate_count: int,
        eligible_count: int,
        returned_count: int,
        results_snapshot: list[dict[str, object]],
        experiment_group: str | None = None,
    ) -> RankingEventRecord:
        event = RankingEventRecord(
            request_id=request_id,
            user_id=user_id,
            ranking_version=ranking_version,
            config_version=config_version,
            taxonomy_version=taxonomy_version,
            experiment_group=experiment_group,
            candidate_count=candidate_count,
            eligible_count=eligible_count,
            returned_count=returned_count,
            results_snapshot_json=results_snapshot,
        )
        self._session.add(event)
        await self._session.flush()
        return event
