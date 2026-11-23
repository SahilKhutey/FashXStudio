from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID


@dataclass
class CustomizationDraft:
    id: UUID
    organization_id: UUID
    menu_id: str
    revision: int
    configuration: dict[str, Any]
    status: str = "draft"
    created_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def etag(self) -> str:
        return f'"revision-{self.revision}"'

    def create_next_revision(self, new_config: dict[str, Any], actor_id: str | None = None) -> "CustomizationDraft":
        return CustomizationDraft(
            id=self.id,
            organization_id=self.organization_id,
            menu_id=self.menu_id,
            revision=self.revision + 1,
            configuration=new_config,
            status="draft",
            created_by=actor_id,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )


@dataclass
class CustomizationRevision:
    id: UUID
    customization_id: UUID
    organization_id: UUID
    menu_id: str
    revision: int
    configuration: dict[str, Any]
    created_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
