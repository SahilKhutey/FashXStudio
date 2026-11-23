import copy
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.modules.customization.application.services.customization_validator import (
    get_customization_validator,
)
from app.modules.customization.application.services.theme_resolver import (
    get_theme_resolver,
)
from app.modules.customization.domain.exceptions import (
    InvalidCustomizationError,
)
from app.modules.customization.infrastructure.persistence.customization_repository import (
    get_customization_repository,
)


class PublishingService:
    def __init__(self) -> None:
        self.validator = get_customization_validator()
        self.resolver = get_theme_resolver()
        self.repository = get_customization_repository()
        self._published_snapshots: dict[tuple[str, str], dict[str, Any]] = {}  # (org_id, menu_id) -> snapshot
        self._publication_history: dict[tuple[str, str], list[dict[str, Any]]] = {}

    def publish_customization(
        self,
        organization_id: UUID,
        menu_id: str,
        configuration: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Publishes a validated menu customization snapshot with pinned versions for ARC-10.
        """
        org_str = str(organization_id)
        # 1. Validate
        val_res = self.validator.validate(configuration)
        if not val_res.is_valid:
            raise InvalidCustomizationError(val_res.errors)

        valid_config = val_res.normalized_configuration or configuration

        # 2. Resolve with exact pinned versions
        resolved = self.resolver.resolve(valid_config, menu_id=menu_id)

        snapshot = {
            "snapshot_id": str(uuid4()),
            "organization_id": org_str,
            "menu_id": menu_id,
            "published_at": datetime.now(UTC).isoformat(),
            "configuration": copy.deepcopy(valid_config),
            "resolved_state": resolved,
        }

        key = (org_str, menu_id)
        self._published_snapshots[key] = copy.deepcopy(snapshot)
        if key not in self._publication_history:
            self._publication_history[key] = []
        self._publication_history[key].append(copy.deepcopy(snapshot))

        return copy.deepcopy(snapshot)

    def get_published_menu(self, organization_id: UUID, menu_id: str) -> dict[str, Any] | None:
        """Public endpoint reads ONLY published snapshot, NEVER draft state."""
        key = (str(organization_id), menu_id)
        snap = self._published_snapshots.get(key)
        return copy.deepcopy(snap) if snap else None

    def rollback_publication(
        self,
        organization_id: UUID,
        menu_id: str,
        target_snapshot_id: str,
    ) -> dict[str, Any]:
        """Rolls back the published menu to an earlier snapshot."""
        key = (str(organization_id), menu_id)
        history = self._publication_history.get(key, [])
        for snap in history:
            if snap["snapshot_id"] == target_snapshot_id:
                self._published_snapshots[key] = copy.deepcopy(snap)
                return copy.deepcopy(snap)
        raise ValueError(f"Snapshot '{target_snapshot_id}' not found in publication history")


_DEFAULT_PUBLISHING_SERVICE = PublishingService()


def get_publishing_service() -> PublishingService:
    return _DEFAULT_PUBLISHING_SERVICE
