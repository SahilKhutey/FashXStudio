"""RC10 privacy and security regression tests."""
from __future__ import annotations

import pytest

from fashx.core.release_config import ReleaseConfig, validate_release_config
from scripts.rc10.validate_metrics import is_eligible_for_pilot_claim


def test_production_release_config_blocks_mock_vto():
    prod_config = ReleaseConfig(
        app_env="production",
        auth_mode="jwks",
        database_url="postgresql+asyncpg://app:secret@db.prod/fashx",
        redis_url="rediss://redis.prod:6379",
        tryon_provider="mock",
        storage_backend="s3",
        cors_origins=["https://app.fashx.com"],
        debug=False,
    )
    with pytest.raises(ValueError, match="mock forbidden"):
        validate_release_config(prod_config)


def test_production_release_config_blocks_sqlite():
    prod_config = ReleaseConfig(
        app_env="production",
        auth_mode="jwks",
        database_url="sqlite+aiosqlite:///fashx_local.db",
        redis_url="rediss://redis.prod:6379",
        tryon_provider="fashn",
        storage_backend="s3",
        cors_origins=["https://app.fashx.com"],
        debug=False,
    )
    with pytest.raises(ValueError, match="requires PostgreSQL database"):
        validate_release_config(prod_config)


def test_privacy_metric_integrity_rejects_synthetic():
    privacy_metric = {
        "metric_name": "data_erasure_adherence_rate",
        "value": 1.0,
        "sample_size": 25,
        "period_start": "2026-11-01T00:00:00+00:00",
        "period_end": "2026-11-05T00:00:00+00:00",
        "extracted_at": "2026-11-05T01:00:00+00:00",
        "evidence_type": "synthetic",
        "source_reference": "synthetic-test-suite",
    }
    assert not is_eligible_for_pilot_claim(privacy_metric)
