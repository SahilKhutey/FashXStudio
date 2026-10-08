from dataclasses import dataclass


@dataclass(frozen=True)
class Engagement:
    user_id: str
    target_id: str
    action: str
    value: str | None = None
