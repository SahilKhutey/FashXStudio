from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

from database.models import Base


def test_expected_foundation_tables_exist() -> None:
    expected = {
        "users",
        "consent_records",
        "user_photos",
        "body_profiles",
        "user_measurements",
        "user_preferences",
        "user_style_profiles",
        "brands",
        "merchants",
        "merchant_products",
        "canonical_garments",
        "merchant_offers",
        "garment_images",
        "garment_enrichments",
        "size_charts",
        "size_measurements",
        "tryon_jobs",
        "tryon_artifacts",
        "wardrobe_items",
        "buy_clicks",
        "fit_feedback",
        "tryon_feedback",
        "feed_exclusions",
        "domain_events",
    }
    assert expected.issubset(set(Base.metadata.tables))


def test_tryon_job_has_idempotency_and_artifact_constraints() -> None:
    table = Base.metadata.tables["tryon_jobs"]
    constraint_names = {c.name for c in table.constraints if c.name}
    assert "uq_tryon_user_idempotency" in constraint_names
    assert "uq_tryon_artifact_key" in constraint_names
