from datetime import datetime, timezone
from uuid import uuid4

from api.app.analytics.application import AnalyticsService
from schemas.analytics.validation import AnalyticsEventCreate, ValidationMetrics


def test_validation_metrics_math():
    metrics = ValidationMetrics(
        window={"start_at": datetime.now(timezone.utc), "end_at": datetime.now(timezone.utc)},
        users_created=10,
        tryon_started=8,
        tryon_completed=6,
        tryon_failed=2,
        tryon_viewed=5,
        tryon_retry_requested=1,
        tryon_feedback_submitted=3,
        wardrobe_saved=2,
        buy_clicks=1,
        unique_tryon_users=5,
        repeat_tryon_users=2,
        unique_session_users=8,
        repeat_session_users=3,
        tryon_completion_rate=0.75,
        result_view_rate=0.8333,
        feedback_rate=0.5,
        save_rate=0.3333,
        buy_click_rate=0.1667,
        repeat_tryon_rate=0.4,
        repeat_session_rate=0.375,
    )
    assert metrics.tryon_completion_rate == 0.75
    assert metrics.repeat_tryon_users == 2


def test_session_event_contract():
    event = AnalyticsEventCreate(event_type="session_started", session_id="session-12345", screen_context="feed")
    assert event.event_type == "session_started"
    assert event.session_id == "session-12345"
