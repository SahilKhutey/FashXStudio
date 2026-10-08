import pytest

from app.core.errors import ValidationError
from fashx.domain.inventory.enums import (
    InventoryStatus,
)
from fashx.domain.inventory.lifecycle import (
    validate_inventory_transition,
)


def test_inventory_activation():
    validate_inventory_transition(
        InventoryStatus.DRAFT,
        InventoryStatus.ACTIVE,
    )


def test_inventory_pause():
    validate_inventory_transition(
        InventoryStatus.ACTIVE,
        InventoryStatus.PAUSED,
    )


def test_inventory_reactivation():
    validate_inventory_transition(
        InventoryStatus.PAUSED,
        InventoryStatus.ACTIVE,
    )


def test_inventory_archive():
    validate_inventory_transition(
        InventoryStatus.DRAFT,
        InventoryStatus.ARCHIVED,
    )
    validate_inventory_transition(
        InventoryStatus.ACTIVE,
        InventoryStatus.ARCHIVED,
    )
    validate_inventory_transition(
        InventoryStatus.PAUSED,
        InventoryStatus.ARCHIVED,
    )


def test_invalid_draft_transition():
    with pytest.raises(ValidationError):
        validate_inventory_transition(
            InventoryStatus.DRAFT,
            InventoryStatus.PAUSED,
        )


def test_archived_inventory_cannot_activate():
    with pytest.raises(ValidationError):
        validate_inventory_transition(
            InventoryStatus.ARCHIVED,
            InventoryStatus.ACTIVE,
        )


def test_archived_inventory_cannot_pause():
    with pytest.raises(ValidationError):
        validate_inventory_transition(
            InventoryStatus.ARCHIVED,
            InventoryStatus.PAUSED,
        )
