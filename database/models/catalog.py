from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin, Vector512


class CatalogSource(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "catalog_sources"

    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)  # api | feed_url | file_drop | manual
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending | cleared | suspended
    rights_display: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rights_tryon: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    image_policy: Mapped[str] = mapped_column(String(32), default="hotlink", nullable=False)  # hotlink | mirror
    refresh_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    max_rps: Mapped[float] = mapped_column(Numeric(5, 2), default=2.0, nullable=False)
    terms_url: Mapped[str | None] = mapped_column(Text)
    terms_checked_on: Mapped[date | None] = mapped_column(Date)
    takedown_contact: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CategoryMap(Base):
    __tablename__ = "category_map"

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="CASCADE"), primary_key=True
    )
    source_category: Mapped[str] = mapped_column(String(255), primary_key=True)
    taxonomy_id: Mapped[str | None] = mapped_column(String(255))


class IngestRun(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ingest_runs"

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="CASCADE"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False)  # running | ok | failed | aborted
    counts: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)


class Brand(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class Merchant(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "merchants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    merchant_type: Mapped[str] = mapped_column(String(64), nullable=False)


class MerchantProduct(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "merchant_products"

    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"), index=True
    )
    brand_id: Mapped[UUID | None] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"))
    source_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_sources.id", ondelete="SET NULL"), index=True
    )
    source_product_id: Mapped[str] = mapped_column(String(255), nullable=False)
    item_group_id: Mapped[str | None] = mapped_column(String(255), index=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    price_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("merchant_id", "source_product_id", name="uq_merchant_product_source"),
    )


class CanonicalGarment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "canonical_garments"

    brand_id: Mapped[UUID | None] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"))
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subcategory: Mapped[str | None] = mapped_column(String(64), index=True)
    gender: Mapped[str] = mapped_column(String(32), default="unisex", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sizes_in_stock: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    tryon_supported: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MerchantOffer(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "merchant_offers"

    garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_garments.id", ondelete="CASCADE"), index=True
    )
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"), index=True
    )
    source_product_id: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class GarmentImage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "garment_images"

    garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_garments.id", ondelete="CASCADE"), index=True
    )
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    perceptual_hash: Mapped[str | None] = mapped_column(String(255))
    image_type: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    __table_args__ = (UniqueConstraint("garment_id", "content_hash", name="uq_garment_image_hash"),)


class GarmentEnrichment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "garment_enrichments"

    garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_garments.id", ondelete="CASCADE"), index=True
    )
    image_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("garment_images.id", ondelete="SET NULL")
    )
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    attributes_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector512(512))
    confidence_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SizeChart(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "size_charts"

    garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_garments.id", ondelete="CASCADE"), index=True
    )
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    parser_version: Mapped[str] = mapped_column(String(64), nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    raw_ocr_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SizeMeasurement(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "size_measurements"

    size_chart_id: Mapped[UUID] = mapped_column(
        ForeignKey("size_charts.id", ondelete="CASCADE"), index=True
    )
    garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("canonical_garments.id", ondelete="CASCADE"), index=True
    )
    size_label: Mapped[str] = mapped_column(String(64), nullable=False)
    chest_cm: Mapped[float | None] = mapped_column()
    length_cm: Mapped[float | None] = mapped_column()
    waist_cm: Mapped[float | None] = mapped_column()
    shoulder_cm: Mapped[float | None] = mapped_column()
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="size_chart")
    confidence: Mapped[float | None] = mapped_column()
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
