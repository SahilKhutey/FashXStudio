from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from .base import Base, UUIDPrimaryKeyMixin

JSONBType = JSON().with_variant(JSONB(), "postgresql")


class ThemeDefinitionRecord(Base):
    __tablename__ = "theme_definitions"
    __table_args__ = (
        UniqueConstraint("id", "version", name="uq_theme_definitions_id_version"),
        Index("ix_theme_definitions_status", "status"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    version: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="active", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens: Mapped[dict[str, Any]] = mapped_column(JSONBType, nullable=False)
    supported_layouts: Mapped[list[str]] = mapped_column(JSONBType, nullable=False)
    supported_components: Mapped[list[str]] = mapped_column(JSONBType, nullable=False)
    accessibility: Mapped[dict[str, Any] | None] = mapped_column(JSONBType, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONBType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LayoutDefinitionRecord(Base):
    __tablename__ = "layout_definitions"
    __table_args__ = (
        UniqueConstraint("id", "version", name="uq_layout_definitions_id_version"),
        Index("ix_layout_definitions_status", "status"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    version: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="active", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    supported_slots: Mapped[list[str]] = mapped_column(JSONBType, nullable=False)
    allowed_components_by_slot: Mapped[dict[str, Any]] = mapped_column(JSONBType, nullable=False)
    default_settings: Mapped[dict[str, Any]] = mapped_column(JSONBType, nullable=False)
    responsive_profiles: Mapped[dict[str, Any]] = mapped_column(JSONBType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ComponentDefinitionRecord(Base):
    __tablename__ = "component_definitions"
    __table_args__ = (
        UniqueConstraint("id", "version", name="uq_component_definitions_id_version"),
        Index("ix_component_definitions_status", "status"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    version: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="active", nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    allowed_slots: Mapped[list[str]] = mapped_column(JSONBType, nullable=False)
    property_schema: Mapped[dict[str, Any]] = mapped_column(JSONBType, nullable=False)
    default_props: Mapped[dict[str, Any]] = mapped_column(JSONBType, nullable=False)
    accessibility: Mapped[dict[str, Any] | None] = mapped_column(JSONBType, nullable=True)
    renderer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MenuCustomizationRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "menu_customizations"
    __table_args__ = (
        UniqueConstraint("organization_id", "menu_id", name="uq_customization_org_menu"),
        Index("ix_menu_customizations_org_menu", "organization_id", "menu_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    menu_id: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="draft", nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONBType, nullable=False)
    created_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CustomizationRevisionRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "customization_revisions"
    __table_args__ = (
        UniqueConstraint("customization_id", "revision", name="uq_revision_customization_rev"),
        Index("ix_customization_revisions_org_menu", "organization_id", "menu_id"),
    )

    customization_id: Mapped[UUID] = mapped_column(
        ForeignKey("menu_customizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    menu_id: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONBType, nullable=False)
    created_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ConfigurationMigrationRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "configuration_migrations"
    __table_args__ = (
        UniqueConstraint("source_version", "target_version", name="uq_migration_source_target"),
    )

    source_version: Mapped[str] = mapped_column(Text, nullable=False)
    target_version: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
