from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    BigInteger,
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

if TYPE_CHECKING:
    from .catalog import (
        CanonicalGarment,
        MerchantOffer,
    )


class OfferStatus(StrEnum):
    ACTIVE = "ACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    INACTIVE = "INACTIVE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    SUSPENDED = "SUSPENDED"


class AvailabilityStatus(StrEnum):
    IN_STOCK = "IN_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    PREORDER = "PREORDER"
    UNKNOWN = "UNKNOWN"


class PriceChangeType(StrEnum):
    INITIAL = "INITIAL"
    PRICE_DROP = "PRICE_DROP"
    PRICE_INCREASE = "PRICE_INCREASE"
    CURRENCY_CHANGE = "CURRENCY_CHANGE"
    DISCOUNT_CHANGE = "DISCOUNT_CHANGE"
    CORRECTION = "CORRECTION"


class SyncStatus(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UPDATE_PENDING = "UPDATE_PENDING"
    SYNC_FAILED = "SYNC_FAILED"
    SOURCE_MISSING = "SOURCE_MISSING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class FreshnessState(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class CatalogTakedownStatus(StrEnum):
    NONE = "NONE"
    REQUESTED = "REQUESTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    UNDER_REVIEW = "UNDER_REVIEW"


class ProvenanceEntityType(StrEnum):
    CANONICAL_GARMENT = "CANONICAL_GARMENT"
    MERCHANT_PRODUCT = "MERCHANT_PRODUCT"
    MERCHANT_OFFER = "MERCHANT_OFFER"
    PRODUCT_VARIANT = "PRODUCT_VARIANT"
    MERCHANT_OFFER_SIZE = "MERCHANT_OFFER_SIZE"


class OfferPriceHistory(Base, UUIDPrimaryKeyMixin):
    """Immutable audit trail of observed offer prices over time."""

    __tablename__ = "merchant_offer_price_history"
    __table_args__ = (
        Index("ix_price_history_offer_observed", "merchant_offer_id", "observed_at"),
        Index("ix_price_history_merchant_source", "merchant_id", "source_id"),
        Index("ix_price_history_recorded", "recorded_at"),
    )

    merchant_offer_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant_offers.id", ondelete="CASCADE"), nullable=False
    )
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="CASCADE"), nullable=False
    )
    ingest_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingest_runs.id", ondelete="SET NULL"), nullable=True
    )

    price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    original_price_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    change_type: Mapped[str] = mapped_column(
        String(32), default=PriceChangeType.INITIAL, nullable=False
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    offer: Mapped[MerchantOffer] = relationship(back_populates="price_history")


class SizeDefinition(Base, UUIDPrimaryKeyMixin):
    """Standardized size classification (e.g. IN / Men's Tops / M)."""

    __tablename__ = "size_definitions"
    __table_args__ = (
        UniqueConstraint(
            "size_system", "category", "standardized_label", name="uq_size_definition"
        ),
        Index("ix_size_definitions_system_cat", "size_system", "category"),
    )

    size_system: Mapped[str] = mapped_column(String(16), nullable=False)  # IN, US, UK, EU
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # tops, bottoms, footwear
    standardized_label: Mapped[str] = mapped_column(String(32), nullable=False)  # XS, S, M, 32, 38
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    variants: Mapped[list[ProductVariant]] = relationship(back_populates="size_definition")
    offer_sizes: Mapped[list[MerchantOfferSize]] = relationship(back_populates="size_definition")


class ProductVariant(Base, UUIDPrimaryKeyMixin):
    """Specific color/size variant belonging to a canonical garment."""

    __tablename__ = "product_variants"
    __table_args__ = (
        Index("ix_product_variants_garment", "canonical_garment_id"),
        Index("ix_product_variants_sku", "sku"),
    )

    canonical_garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_garments.id", ondelete="CASCADE"), nullable=False
    )
    sku: Mapped[str | None] = mapped_column(String(128), nullable=True)
    color: Mapped[str | None] = mapped_column(String(64), nullable=True)
    color_hex: Mapped[str | None] = mapped_column(String(7), nullable=True)
    size_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_definition_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("size_definitions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    canonical_garment: Mapped[CanonicalGarment] = relationship(back_populates="variants")
    size_definition: Mapped[SizeDefinition | None] = relationship(back_populates="variants")
    offer_sizes: Mapped[list[MerchantOfferSize]] = relationship(back_populates="variant")


class MerchantOfferSize(Base, UUIDPrimaryKeyMixin):
    """Merchant-reported size stock and availability for a specific offer."""

    __tablename__ = "merchant_offer_sizes"
    __table_args__ = (
        UniqueConstraint("merchant_offer_id", "raw_size", name="uq_offer_raw_size"),
        Index("ix_offer_sizes_size_availability", "size_definition_id", "availability"),
        Index("ix_offer_sizes_offer", "merchant_offer_id"),
    )

    merchant_offer_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant_offers.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True
    )
    size_definition_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("size_definitions.id", ondelete="SET NULL"), nullable=True
    )
    raw_size: Mapped[str] = mapped_column(String(64), nullable=False)
    size_system: Mapped[str | None] = mapped_column(String(16), nullable=True)
    availability: Mapped[str] = mapped_column(
        String(32), default=AvailabilityStatus.IN_STOCK, server_default="IN_STOCK", nullable=False
    )
    stock_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    offer: Mapped[MerchantOffer] = relationship(back_populates="offer_sizes")
    variant: Mapped[ProductVariant | None] = relationship(back_populates="offer_sizes")
    size_definition: Mapped[SizeDefinition | None] = relationship(back_populates="offer_sizes")


class CatalogProvenanceRecord(Base, UUIDPrimaryKeyMixin):
    """Detailed attribution for individual canonical or merchant product attributes."""

    __tablename__ = "catalog_provenance_records"
    __table_args__ = (
        Index("ix_provenance_entity_attr", "entity_type", "entity_id", "attribute_name"),
        Index("ix_provenance_source", "source_id"),
        Index("ix_provenance_run", "ingest_run_id"),
    )

    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(nullable=False)
    attribute_name: Mapped[str] = mapped_column(String(64), nullable=False)
    attribute_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="CASCADE"), nullable=False
    )
    merchant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True
    )
    ingest_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingest_runs.id", ondelete="SET NULL"), nullable=True
    )
    confidence: Mapped[float] = mapped_column(
        Numeric(4, 3), default=1.0, server_default="1.000", nullable=False
    )
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
