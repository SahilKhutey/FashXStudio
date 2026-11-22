from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin


class TaxonomyVersion(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "taxonomy_versions"

    version: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", server_default="ACTIVE", nullable=False
    )
    locale: Mapped[str] = mapped_column(
        String(16), default="en-IN", server_default="en-IN", nullable=False
    )
    market: Mapped[str] = mapped_column(
        String(16), default="IN", server_default="IN", nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, server_default="{}", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    categories: Mapped[list[TaxonomyCategory]] = relationship(
        back_populates="version_record", cascade="all, delete-orphan"
    )
    attributes: Mapped[list[TaxonomyAttribute]] = relationship(
        back_populates="version_record", cascade="all, delete-orphan"
    )
    aliases: Mapped[list[TaxonomyAlias]] = relationship(
        back_populates="version_record", cascade="all, delete-orphan"
    )


class TaxonomyCategory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "taxonomy_categories"

    taxonomy_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("taxonomy_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_code: Mapped[str] = mapped_column(String(64), nullable=False)
    parent_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    is_leaf: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "taxonomy_version_id", "category_code", name="uq_taxonomy_category_version_code"
        ),
        Index("ix_taxonomy_categories_path", "path"),
    )

    version_record: Mapped[TaxonomyVersion] = relationship(back_populates="categories")


class TaxonomyAttribute(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "taxonomy_attributes"

    taxonomy_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("taxonomy_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attribute_code: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    attribute_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    is_multi_valued: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    allowed_categories: Mapped[list] = mapped_column(
        JSON, default=list, server_default="[]", nullable=False
    )
    validation_rules: Mapped[dict] = mapped_column(
        JSON, default=dict, server_default="{}", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "taxonomy_version_id", "attribute_code", name="uq_taxonomy_attribute_version_code"
        ),
    )

    version_record: Mapped[TaxonomyVersion] = relationship(back_populates="attributes")
    values: Mapped[list[TaxonomyAttributeValueRecord]] = relationship(
        back_populates="attribute_record", cascade="all, delete-orphan"
    )


class TaxonomyAttributeValueRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "taxonomy_attribute_values"

    attribute_id: Mapped[UUID] = mapped_column(
        ForeignKey("taxonomy_attributes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value_code: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    parent_value_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, server_default="{}", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("attribute_id", "value_code", name="uq_taxonomy_attr_value_code"),
    )

    attribute_record: Mapped[TaxonomyAttribute] = relationship(back_populates="values")


class TaxonomyAlias(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "taxonomy_aliases"

    taxonomy_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("taxonomy_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_code: Mapped[str] = mapped_column(String(64), nullable=False)
    alias_term: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="merchant", server_default="merchant", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_taxonomy_aliases_lookup", "taxonomy_version_id", "target_type", "alias_term"),
    )

    version_record: Mapped[TaxonomyVersion] = relationship(back_populates="aliases")


class ProductClassificationRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "product_classifications"

    garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_garments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    taxonomy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    category_id: Mapped[str] = mapped_column(String(64), nullable=False)
    garment_type_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    style_family: Mapped[str | None] = mapped_column(String(64), nullable=True)
    intended_audience: Mapped[str | None] = mapped_column(String(32), nullable=True)
    occasions: Mapped[list] = mapped_column(JSON, default=list, server_default="[]", nullable=False)
    classification_status: Mapped[str] = mapped_column(
        String(32), default="VERIFIED", server_default="VERIFIED", nullable=False
    )
    classification_source: Mapped[str] = mapped_column(
        String(32), default="MERCHANT", server_default="MERCHANT", nullable=False
    )
    classification_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    classified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "garment_id", "taxonomy_version", name="uq_product_classifications_garment_version"
        ),
        Index("ix_product_classifications_cat", "category_id", "garment_type_id"),
    )

    attributes: Mapped[list[ProductAttributeValueRecord]] = relationship(
        back_populates="classification_record", cascade="all, delete-orphan"
    )


class ProductAttributeValueRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "product_attribute_values"

    classification_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_classifications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attribute_code: Mapped[str] = mapped_column(String(64), nullable=False)
    value_status: Mapped[str] = mapped_column(
        String(32), default="KNOWN", server_default="KNOWN", nullable=False
    )
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "classification_id", "attribute_code", name="uq_product_attr_classification_code"
        ),
        Index("ix_product_attr_values_lookup", "attribute_code", "value_status"),
    )

    classification_record: Mapped[ProductClassificationRecord] = relationship(
        back_populates="attributes"
    )
    provenance_records: Mapped[list[ProductAttributeProvenanceRecord]] = relationship(
        back_populates="attribute_value_record", cascade="all, delete-orphan"
    )


class ProductAttributeProvenanceRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "product_attribute_provenance"

    product_attribute_value_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_attribute_values.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(32), default="UNREVIEWED", server_default="UNREVIEWED", nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, server_default="{}", nullable=False
    )

    attribute_value_record: Mapped[ProductAttributeValueRecord] = relationship(
        back_populates="provenance_records"
    )
