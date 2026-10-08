from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDPrimaryKeyMixin, Vector512


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

    merchant_id: Mapped[UUID] = mapped_column(ForeignKey("merchants.id", ondelete="CASCADE"), index=True)
    brand_id: Mapped[UUID | None] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"))
    source_product_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("merchant_id", "source_product_id", name="uq_merchant_product_source"),)


class CanonicalGarment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "canonical_garments"

    brand_id: Mapped[UUID | None] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"))
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subcategory: Mapped[str | None] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MerchantOffer(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "merchant_offers"

    garment_id: Mapped[UUID] = mapped_column(ForeignKey("canonical_garments.id", ondelete="CASCADE"), index=True)
    merchant_id: Mapped[UUID] = mapped_column(ForeignKey("merchants.id", ondelete="CASCADE"), index=True)
    source_product_id: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GarmentImage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "garment_images"

    garment_id: Mapped[UUID] = mapped_column(ForeignKey("canonical_garments.id", ondelete="CASCADE"), index=True)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    perceptual_hash: Mapped[str | None] = mapped_column(String(255))
    image_type: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    __table_args__ = (UniqueConstraint("garment_id", "content_hash", name="uq_garment_image_hash"),)


class GarmentEnrichment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "garment_enrichments"

    garment_id: Mapped[UUID] = mapped_column(ForeignKey("canonical_garments.id", ondelete="CASCADE"), index=True)
    image_id: Mapped[UUID | None] = mapped_column(ForeignKey("garment_images.id", ondelete="SET NULL"))
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    attributes_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector512(512))
    confidence_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SizeChart(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "size_charts"

    garment_id: Mapped[UUID] = mapped_column(ForeignKey("canonical_garments.id", ondelete="CASCADE"), index=True)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    parser_version: Mapped[str] = mapped_column(String(64), nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    raw_ocr_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SizeMeasurement(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "size_measurements"

    size_chart_id: Mapped[UUID] = mapped_column(ForeignKey("size_charts.id", ondelete="CASCADE"), index=True)
    garment_id: Mapped[UUID] = mapped_column(ForeignKey("canonical_garments.id", ondelete="CASCADE"), index=True)
    size_label: Mapped[str] = mapped_column(String(64), nullable=False)
    chest_cm: Mapped[float | None] = mapped_column()
    length_cm: Mapped[float | None] = mapped_column()
    waist_cm: Mapped[float | None] = mapped_column()
    shoulder_cm: Mapped[float | None] = mapped_column()
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="size_chart")
    confidence: Mapped[float | None] = mapped_column()
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
