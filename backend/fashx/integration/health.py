from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ComponentHealth:
    name: str
    status: str
    details: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SystemHealth:
    status: str
    components: tuple[ComponentHealth, ...]


def evaluate_system_health(runtime: Any) -> SystemHealth:
    components: list[ComponentHealth] = []
    all_healthy = True

    required = [
        "product_service",
        "commerce_service",
        "pricing_service",
        "cart_service",
        "checkout_service",
        "order_service",
        "payment_service",
        "fulfillment_service",
        "customer_service",
        "recommendation_service",
        "trend_service",
        "analytics_service",
    ]

    for comp_name in required:
        is_registered = runtime.registry.contains(comp_name)
        status = "healthy" if is_registered else "unhealthy"
        if not is_registered:
            all_healthy = False
        components.append(
            ComponentHealth(
                name=comp_name,
                status=status,
                details={"registered": str(is_registered)},
            )
        )

    return SystemHealth(
        status="healthy" if all_healthy else "degraded",
        components=tuple(components),
    )
