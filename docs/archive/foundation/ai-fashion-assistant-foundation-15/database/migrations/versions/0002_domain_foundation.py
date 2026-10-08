"""add shared domain foundation tables

Revision ID: 0002_domain_foundation
Revises: 0001_foundation
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_domain_foundation"
down_revision: str | Sequence[str] | None = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "consent_records",
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("data_type", sa.String(length=64), primary_key=True),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "user_photos",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("photo_type", sa.String(length=32), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reject_reason", sa.Text()),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_photos_user_id", "user_photos", ["user_id", "photo_type"])

    op.create_table(
        "body_profiles",
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("height_cm", sa.Integer()),
        sa.Column("weight_kg", sa.Integer()),
        sa.Column("build", sa.String(length=32)),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_table(
        "user_measurements",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("measurement", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float()),
    )
    op.create_index("ix_user_measurements_user_id", "user_measurements", ["user_id"])
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("colors_favored", sa.JSON(), nullable=False),
        sa.Column("colors_avoided", sa.JSON(), nullable=False),
        sa.Column("categories", sa.JSON(), nullable=False),
        sa.Column("budget_min", sa.Integer()),
        sa.Column("budget_max", sa.Integer()),
    )
    op.create_table(
        "user_style_profiles",
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("embedding", sa.Text()),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )

    op.create_table(
        "brands",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False, unique=True),
    )
    op.create_table(
        "merchants",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("merchant_type", sa.String(length=64), nullable=False),
    )
    op.create_table(
        "merchant_products",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("merchant_id", sa.UUID(), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("brand_id", sa.UUID(), sa.ForeignKey("brands.id", ondelete="SET NULL")),
        sa.Column("source_product_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("merchant_id", "source_product_id", name="uq_merchant_product_source"),
    )
    op.create_index("ix_merchant_products_merchant_id", "merchant_products", ["merchant_id"])
    op.create_table(
        "canonical_garments",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("brand_id", sa.UUID(), sa.ForeignKey("brands.id", ondelete="SET NULL")),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("subcategory", sa.String(length=64)),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_canonical_garments_category", "canonical_garments", ["category", "subcategory"])
    op.create_table(
        "merchant_offers",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("garment_id", sa.UUID(), sa.ForeignKey("canonical_garments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("merchant_id", sa.UUID(), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_product_id", sa.String(length=255), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("in_stock", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_merchant_offers_garment_id", "merchant_offers", ["garment_id"])
    op.create_index("ix_merchant_offers_merchant_id", "merchant_offers", ["merchant_id"])
    op.create_table(
        "garment_images",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("garment_id", sa.UUID(), sa.ForeignKey("canonical_garments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("perceptual_hash", sa.String(length=255)),
        sa.Column("image_type", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("garment_id", "content_hash", name="uq_garment_image_hash"),
    )
    op.create_index("ix_garment_images_garment_id", "garment_images", ["garment_id"])
    op.create_index("ix_garment_images_content_hash", "garment_images", ["content_hash"])
    op.create_table(
        "garment_enrichments",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("garment_id", sa.UUID(), sa.ForeignKey("canonical_garments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_id", sa.UUID(), sa.ForeignKey("garment_images.id", ondelete="SET NULL")),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("attributes_json", sa.JSON(), nullable=False),
        sa.Column("embedding", sa.Text()),
        sa.Column("confidence_summary", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_garment_enrichments_garment_id", "garment_enrichments", ["garment_id"])
    op.create_table(
        "size_charts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("garment_id", sa.UUID(), sa.ForeignKey("canonical_garments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("parser_version", sa.String(length=64), nullable=False),
        sa.Column("review_status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("raw_ocr_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_size_charts_garment_id", "size_charts", ["garment_id"])
    op.create_table(
        "size_measurements",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("size_chart_id", sa.UUID(), sa.ForeignKey("size_charts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("garment_id", sa.UUID(), sa.ForeignKey("canonical_garments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("size_label", sa.String(length=64), nullable=False),
        sa.Column("chest_cm", sa.Float()),
        sa.Column("length_cm", sa.Float()),
        sa.Column("waist_cm", sa.Float()),
        sa.Column("shoulder_cm", sa.Float()),
        sa.Column("source", sa.String(length=32), server_default="size_chart", nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("needs_review", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index("ix_size_measurements_garment_id", "size_measurements", ["garment_id"])

    op.create_table(
        "tryon_jobs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("garment_id", sa.UUID(), sa.ForeignKey("canonical_garments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_photo_id", sa.UUID(), sa.ForeignKey("user_photos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("artifact_key", sa.String(length=512), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("pipeline_version", sa.String(length=64), nullable=False),
        sa.Column("failure_reason", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_tryon_user_idempotency"),
    )
    op.create_index("ix_tryon_jobs_user_id", "tryon_jobs", ["user_id", "created_at"])
    op.create_table(
        "tryon_artifacts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("job_id", sa.UUID(), sa.ForeignKey("tryon_jobs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("artifact_key", sa.String(length=512), nullable=False, unique=True),
        sa.Column("result_key", sa.Text(), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("pipeline_version", sa.String(length=64), nullable=False),
        sa.Column("photo_version", sa.Integer(), nullable=False),
        sa.Column("garment_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "wardrobe_items",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("garment_id", sa.UUID(), sa.ForeignKey("canonical_garments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("offer_id", sa.UUID(), sa.ForeignKey("merchant_offers.id", ondelete="SET NULL")),
        sa.Column("tryon_artifact_id", sa.UUID(), sa.ForeignKey("tryon_artifacts.id", ondelete="SET NULL")),
        sa.Column("snapshot_title", sa.Text(), nullable=False),
        sa.Column("snapshot_price_minor", sa.Integer(), nullable=False),
        sa.Column("snapshot_currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("snapshot_image_key", sa.Text(), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_wardrobe_items_user_id", "wardrobe_items", ["user_id"])

    op.create_table(
        "buy_clicks",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("garment_id", sa.UUID(), sa.ForeignKey("canonical_garments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("offer_id", sa.UUID(), sa.ForeignKey("merchant_offers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("affiliate_network", sa.String(length=64)),
        sa.Column("tracking_id", sa.String(length=255)),
        sa.Column("clicked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_buy_clicks_user_id", "buy_clicks", ["user_id"])

    op.create_table(
        "fit_feedback",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("garment_id", sa.UUID(), sa.ForeignKey("canonical_garments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("brand_id", sa.UUID(), sa.ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("buy_click_id", sa.UUID(), sa.ForeignKey("buy_clicks.id", ondelete="SET NULL")),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("fit_type", sa.String(length=64)),
        sa.Column("size_label", sa.String(length=64), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_fit_feedback_user_id", "fit_feedback", ["user_id"])
    op.create_index("ix_fit_feedback_brand_size", "fit_feedback", ["brand_id", "category", "fit_type", "size_label"])
    op.create_table(
        "tryon_feedback",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tryon_job_id", sa.UUID(), sa.ForeignKey("tryon_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("visual_accuracy", sa.String(length=32), nullable=False),
        sa.Column("purchase_confidence", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tryon_feedback_user_id", "tryon_feedback", ["user_id"])
    op.create_table(
        "feed_exclusions",
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("garment_id", sa.UUID(), sa.ForeignKey("canonical_garments.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("reason", sa.String(length=64), server_default="rejected", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    # Convert textual placeholders to native pgvector columns after table creation.
    # The 0001 migration guarantees the extension is installed before this migration runs.
    op.execute("ALTER TABLE user_style_profiles ALTER COLUMN embedding TYPE vector(512) USING NULLIF(embedding, '')::vector")
    op.execute("ALTER TABLE garment_enrichments ALTER COLUMN embedding TYPE vector(512) USING NULLIF(embedding, '')::vector")

    op.create_table(
        "domain_events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("object_type", sa.String(length=64)),
        sa.Column("object_id", sa.UUID()),
        sa.Column("trace_id", sa.UUID()),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_domain_events_event_type", "domain_events", ["event_type", "occurred_at"])
    op.create_index("ix_domain_events_user_id", "domain_events", ["user_id", "occurred_at"])
    op.create_index("ix_domain_events_trace_id", "domain_events", ["trace_id"])


def downgrade() -> None:
    for table in [
        "domain_events", "feed_exclusions", "tryon_feedback", "fit_feedback", "buy_clicks", "wardrobe_items",
        "tryon_artifacts", "tryon_jobs", "size_measurements", "size_charts", "garment_enrichments",
        "garment_images", "merchant_offers", "canonical_garments", "merchant_products", "merchants", "brands",
        "user_style_profiles", "user_preferences", "user_measurements", "body_profiles", "user_photos", "consent_records", "users",
    ]:
        op.drop_table(table)
