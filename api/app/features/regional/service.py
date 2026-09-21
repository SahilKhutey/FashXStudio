from .models import RegionalContext


class RegionalService:
    """F12 context store. Geocoding/weather providers plug in above this contract."""

    def __init__(self) -> None:
        self._contexts: dict[str, RegionalContext] = {}

    def set_context(self, user_id: str, context: RegionalContext) -> RegionalContext:
        if not user_id.strip() or not context.region.strip():
            raise ValueError("user_id and region are required")
        self._contexts[user_id] = context
        return context

    def get_context(self, user_id: str) -> RegionalContext | None:
        return self._contexts.get(user_id)
