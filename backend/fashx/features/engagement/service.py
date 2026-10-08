from .models import Engagement


class EngagementService:
    """F13 interaction ledger; delivery channels remain notification adapters."""

    ALLOWED_ACTIONS = frozenset({"like", "follow", "review", "share"})

    def __init__(self) -> None:
        self._events: list[Engagement] = []

    def record(self, event: Engagement) -> Engagement:
        if not event.user_id.strip() or not event.target_id.strip():
            raise ValueError("user_id and target_id are required")
        if event.action not in self.ALLOWED_ACTIONS:
            raise ValueError("Unsupported engagement action")
        self._events.append(event)
        return event

    def events_for(self, user_id: str) -> tuple[Engagement, ...]:
        return tuple(event for event in self._events if event.user_id == user_id)
