from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from api.app.core.transactions import transaction
from api.app.events.repository import EventRepository
from api.app.analytics.repository import AnalyticsRepository
from schemas.analytics.validation import AnalyticsEventCreate, AnalyticsEventResponse, AnalyticsWindow, ValidationMetrics


class AnalyticsService:
    def __init__(self, session, repository: AnalyticsRepository) -> None:
        self.session = session
        self.repository = repository

    async def record_session_event(
        self,
        *,
        user_id: UUID,
        request: AnalyticsEventCreate,
        trace_id: UUID | None,
    ) -> AnalyticsEventResponse:
        async with transaction(self.session):
            await EventRepository(self.session).create(
                event_id=uuid4(),
                event_type=request.event_type,
                schema_version=1,
                user_id=user_id,
                object_type="session",
                object_id=None,
                trace_id=trace_id,
                occurred_at=datetime.now(timezone.utc),
                payload={"session_id": request.session_id, "screen_context": request.screen_context},
            )
        return AnalyticsEventResponse()

    async def validation_metrics(self, *, start_at: datetime, end_at: datetime) -> ValidationMetrics:
        if start_at.tzinfo is None or end_at.tzinfo is None:
            raise ValueError("Analytics window timestamps must include timezone")
        counts = await self.repository.event_counts(start_at, end_at)
        users_created = await self.repository.count_users_created(start_at, end_at)
        feedback = await self.repository.count_feedback(start_at, end_at)
        saves = await self.repository.count_saves(start_at, end_at)
        buy_clicks = await self.repository.count_buy_clicks(start_at, end_at)
        unique_tryon_users = await self.repository.distinct_event_users("tryon_started", start_at, end_at)
        repeat_tryon_users = await self.repository.repeat_event_users("tryon_started", start_at, end_at)
        unique_session_users = await self.repository.distinct_event_users("session_started", start_at, end_at)
        repeat_session_users = await self.repository.repeat_event_users("session_started", start_at, end_at)

        started = counts.get("tryon_started", 0)
        completed = counts.get("tryon_completed", 0)
        viewed = counts.get("tryon_viewed", 0)
        feedback_submitted = counts.get("tryon_feedback_submitted", 0)

        def rate(numerator: int, denominator: int) -> float:
            return round(numerator / denominator, 4) if denominator else 0.0

        return ValidationMetrics(
            window=AnalyticsWindow(start_at=start_at, end_at=end_at),
            users_created=users_created,
            tryon_started=started,
            tryon_completed=completed,
            tryon_failed=counts.get("tryon_failed", 0),
            tryon_viewed=viewed,
            tryon_retry_requested=counts.get("tryon_retry_requested", 0),
            tryon_feedback_submitted=feedback_submitted,
            wardrobe_saved=saves,
            buy_clicks=buy_clicks,
            unique_tryon_users=unique_tryon_users,
            repeat_tryon_users=repeat_tryon_users,
            unique_session_users=unique_session_users,
            repeat_session_users=repeat_session_users,
            tryon_completion_rate=rate(completed, started),
            result_view_rate=rate(viewed, completed),
            feedback_rate=rate(feedback_submitted, completed),
            save_rate=rate(saves, completed),
            buy_click_rate=rate(buy_clicks, completed),
            repeat_tryon_rate=rate(repeat_tryon_users, unique_tryon_users),
            repeat_session_rate=rate(repeat_session_users, unique_session_users),
        )
