from dataclasses import dataclass


@dataclass(frozen=True)
class RegionalContext:
    region: str
    climate: str | None = None
    season: str | None = None
    locality: str | None = None
