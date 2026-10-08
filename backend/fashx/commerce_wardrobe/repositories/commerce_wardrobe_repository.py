from collections.abc import Callable, Sequence
from uuid import UUID

from api.app.core.repository import BaseRepository
from api.app.core.unit_of_work import SqlAlchemyUnitOfWork
from database.models.commerce_feedback import (
    BuyClick,
    FitFeedback,
    TryOnFeedback,
    WardrobeItem,
)
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class WardrobeRepository(BaseRepository[WardrobeItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, WardrobeItem)

    async def list_for_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> Sequence[WardrobeItem]:
        stmt = (
            select(WardrobeItem)
            .where(WardrobeItem.user_id == user_id)
            .order_by(desc(WardrobeItem.saved_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def get_by_user_and_garment(self, user_id: UUID, garment_id: UUID) -> WardrobeItem | None:
        stmt = select(WardrobeItem).where(
            WardrobeItem.user_id == user_id,
            WardrobeItem.garment_id == garment_id,
        )
        return await self.session.scalar(stmt)


class BuyClickRepository(BaseRepository[BuyClick]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, BuyClick)

    async def list_for_user(self, user_id: UUID, limit: int = 50) -> Sequence[BuyClick]:
        stmt = (
            select(BuyClick)
            .where(BuyClick.user_id == user_id)
            .order_by(desc(BuyClick.clicked_at))
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        return result.all()


class FitFeedbackRepository(BaseRepository[FitFeedback]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, FitFeedback)

    async def list_for_brand(
        self, brand_id: UUID, category: str | None = None
    ) -> Sequence[FitFeedback]:
        stmt = select(FitFeedback).where(FitFeedback.brand_id == brand_id)
        if category:
            stmt = stmt.where(FitFeedback.category == category)
        result = await self.session.scalars(stmt)
        return result.all()

    async def compute_brand_bias(
        self, brand_id: UUID, category: str | None = None
    ) -> dict[str, float | int | str]:
        feedbacks = await self.list_for_brand(brand_id, category)
        total = len(feedbacks)
        if total == 0:
            return {
                "total_observations": 0,
                "bias_score": 0.0,
                "recommendation": "true_to_size",
                "too_tight_pct": 0.0,
                "true_to_size_pct": 0.0,
                "too_loose_pct": 0.0,
            }

        too_tight = sum(1 for f in feedbacks if f.verdict == "too_tight")
        true_to_size = sum(1 for f in feedbacks if f.verdict == "true_to_size")
        too_loose = sum(1 for f in feedbacks if f.verdict == "too_loose")

        # Bias Score Formula (Roadmap 5.3): (too_loose - too_tight) / total
        # Negative bias => brand runs small (advise size up)
        # Positive bias => brand runs large (advise size down)
        bias_score = round((too_loose - too_tight) / total, 3)

        if bias_score < -0.3:
            recommendation = "size_up"
        elif bias_score > 0.3:
            recommendation = "size_down"
        else:
            recommendation = "true_to_size"

        return {
            "total_observations": total,
            "bias_score": bias_score,
            "recommendation": recommendation,
            "too_tight_pct": round(too_tight / total * 100, 1),
            "true_to_size_pct": round(true_to_size / total * 100, 1),
            "too_loose_pct": round(too_loose / total * 100, 1),
        }


class TryOnFeedbackRepository(BaseRepository[TryOnFeedback]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TryOnFeedback)

    async def get_by_job_id(self, job_id: UUID) -> TryOnFeedback | None:
        stmt = select(TryOnFeedback).where(TryOnFeedback.tryon_job_id == job_id)
        return await self.session.scalar(stmt)


class CommerceWardrobeUnitOfWork(SqlAlchemyUnitOfWork):
    """Unit of work managing Commerce, Wardrobe, and Feedback persistence."""

    def __init__(
        self,
        session_factory: (
            Callable[[], AsyncSession] | async_sessionmaker[AsyncSession] | None
        ) = None,
    ) -> None:
        super().__init__(session_factory)
        self._wardrobe: WardrobeRepository | None = None
        self._buy_clicks: BuyClickRepository | None = None
        self._fit_feedback: FitFeedbackRepository | None = None
        self._tryon_feedback: TryOnFeedbackRepository | None = None

    async def __aenter__(self) -> "CommerceWardrobeUnitOfWork":
        await super().__aenter__()
        self._wardrobe = None
        self._buy_clicks = None
        self._fit_feedback = None
        self._tryon_feedback = None
        return self

    @property
    def wardrobe(self) -> WardrobeRepository:
        if self._wardrobe is None:
            self._wardrobe = WardrobeRepository(self.session)
        return self._wardrobe

    @property
    def buy_clicks(self) -> BuyClickRepository:
        if self._buy_clicks is None:
            self._buy_clicks = BuyClickRepository(self.session)
        return self._buy_clicks

    @property
    def fit_feedback(self) -> FitFeedbackRepository:
        if self._fit_feedback is None:
            self._fit_feedback = FitFeedbackRepository(self.session)
        return self._fit_feedback

    @property
    def tryon_feedback(self) -> TryOnFeedbackRepository:
        if self._tryon_feedback is None:
            self._tryon_feedback = TryOnFeedbackRepository(self.session)
        return self._tryon_feedback
