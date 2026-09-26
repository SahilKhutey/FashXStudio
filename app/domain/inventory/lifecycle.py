from __future__ import annotations

from app.core.errors import ValidationError

from .enums import InventoryStatus

_INVENTORY_TRANSITIONS = {
    InventoryStatus.DRAFT: {
        InventoryStatus.ACTIVE,
        InventoryStatus.ARCHIVED,
    },
    InventoryStatus.ACTIVE: {
        InventoryStatus.PAUSED,
        InventoryStatus.ARCHIVED,
    },
    InventoryStatus.PAUSED: {
        InventoryStatus.ACTIVE,
        InventoryStatus.ARCHIVED,
    },
    InventoryStatus.ARCHIVED: set(),
}


def validate_inventory_transition(
    current: InventoryStatus,
    target: InventoryStatus,
) -> None:

    if target not in _INVENTORY_TRANSITIONS[current]:

        raise ValidationError(
            "Invalid inventory status transition.",
            {
                "current": current.value,
                "target": target.value,
            },
        )
