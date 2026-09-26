from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from app.core.contracts import Entity
from app.core.errors import ValidationError
from app.core.ids import new_id

from .enums import ClassificationSource, TaxonomyStatus, TaxonomyType


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class TaxonomyNode(Entity):
    id: UUID = field(default_factory=new_id)

    name: str = ""
    slug: str = ""

    taxonomy_type: TaxonomyType = TaxonomyType.CATEGORY

    parent_id: UUID | None = None

    description: str | None = None

    status: TaxonomyStatus = TaxonomyStatus.ACTIVE

    metadata: dict[str, str] = field(default_factory=dict)

    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    version: int = 1

    def validate(self) -> None:
        if not self.name.strip():
            raise ValidationError(
                "Taxonomy name cannot be empty.",
                {"field": "name"},
            )

        if not self.slug.strip():
            raise ValidationError(
                "Taxonomy slug cannot be empty.",
                {"field": "slug"},
            )

        if len(self.name) > 200:
            raise ValidationError(
                "Taxonomy name cannot exceed 200 characters.",
                {"field": "name"},
            )

        if len(self.slug) > 200:
            raise ValidationError(
                "Taxonomy slug cannot exceed 200 characters.",
                {"field": "slug"},
            )

        if self.version < 1:
            raise ValidationError(
                "Taxonomy version must be positive.",
                {"field": "version"},
            )

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1


@dataclass(frozen=True, slots=True)
class FashionAttribute:
    key: str
    value: str

    def validate(self) -> None:
        if not self.key.strip():
            raise ValidationError(
                "Fashion attribute key cannot be empty."
            )

        if not self.value.strip():
            raise ValidationError(
                "Fashion attribute value cannot be empty."
            )


@dataclass(slots=True)
class ProductFashionProfile(Entity):
    id: UUID = field(default_factory=new_id)

    product_id: UUID | None = None

    taxonomy_node_ids: set[UUID] = field(default_factory=set)

    attributes: list[FashionAttribute] = field(
        default_factory=list
    )

    source: ClassificationSource = ClassificationSource.MANUAL

    confidence: float | None = None

    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    version: int = 1

    def validate(self) -> None:
        if self.product_id is None:
            raise ValidationError(
                "Product ID is required for fashion classification."
            )

        if self.confidence is not None:
            if not 0.0 <= self.confidence <= 1.0:
                raise ValidationError(
                    "Classification confidence must be between 0 and 1.",
                    {"field": "confidence"},
                )

        for attribute in self.attributes:
            attribute.validate()

        if self.version < 1:
            raise ValidationError(
                "Profile version must be positive."
            )

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1
