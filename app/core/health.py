from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

HealthStatus = Literal["healthy", "degraded", "unhealthy"]


@dataclass(frozen=True, slots=True)
class HealthReport:
    component: str
    status: HealthStatus
    version: str
    details: dict[str, str]


def core_health() -> HealthReport:
    from .version import CORE_VERSION

    return HealthReport(
        component="fashxstudio-core",
        status="healthy",
        version=CORE_VERSION,
        details={
            "event_bus": "ready",
            "registry": "ready",
            "contracts": "ready",
        },
    )
