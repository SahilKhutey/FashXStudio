import pytest
from pydantic import ValidationError

from fashx.core.settings import Settings
from fashx.ml.licenses import assert_production_license
from fashx.tryon.adapters.mock_adapter import MockAdapter, MockTryOnAdapter


def test_prod_rejects_mock_and_research_licenses():
    # MockAdapter declares "mock"
    with pytest.raises(RuntimeError, match="not allowed in production"):
        assert_production_license(MockAdapter())

    with pytest.raises(RuntimeError, match="not allowed in production"):
        assert_production_license(MockTryOnAdapter())

    class NonCommercialAdapter:
        license_id = "cc-by-nc-sa"

    with pytest.raises(RuntimeError, match="not allowed in production"):
        assert_production_license(NonCommercialAdapter())


def test_allowed_commercial_and_open_licenses_pass():
    class CommercialApiAdapter:
        license_id = "commercial-api"

    assert_production_license(CommercialApiAdapter())

    class ApacheAdapter:
        license_id = "apache-2.0"

    assert_production_license(ApacheAdapter())


def test_prod_settings_reject_mock_provider(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("REPO_BACKEND", "sql")
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("S3_BUCKET", "prod-bucket")
    monkeypatch.setenv("S3_ACCESS_KEY_ID", "key-id")
    monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "secret-key")
    monkeypatch.setenv("AUTH_MODE", "jwks")
    monkeypatch.setenv("AUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("TRYON_PROVIDER", "mock")

    with pytest.raises(ValidationError, match="prod requires non-mock TRYON_PROVIDER"):
        Settings()
