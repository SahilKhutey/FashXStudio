import pytest
from pydantic import ValidationError

from fashx.core.settings import Settings


def set_prod_env(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("REPO_BACKEND", "sql")
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("S3_BUCKET", "fashx-media-prod")
    monkeypatch.setenv("S3_USE_IAM_ROLE", "true")
    monkeypatch.setenv("AUTH_MODE", "jwks")
    monkeypatch.setenv("AUTH_JWKS_URL", "https://ref.supabase.co/auth/v1/.well-known/jwks.json")
    monkeypatch.setenv("AUTH_ISSUER", "https://ref.supabase.co/auth/v1")
    monkeypatch.setenv("AUTH_AUDIENCE", "authenticated")
    monkeypatch.setenv("TRYON_PROVIDER", "fashn_selfhost")
    monkeypatch.setenv("CORS_ORIGINS", '["https://app.fashxstudio.com"]')


def test_prod_accepts_valid_production_config(monkeypatch):
    set_prod_env(monkeypatch)
    cfg = Settings()
    assert cfg.env == "prod"
    assert cfg.is_production is True


def test_prod_refuses_memory_repo(monkeypatch):
    set_prod_env(monkeypatch)
    monkeypatch.setenv("REPO_BACKEND", "memory")
    with pytest.raises(ValidationError, match="prod requires REPO_BACKEND=sql"):
        Settings()


def test_prod_refuses_local_storage(monkeypatch):
    set_prod_env(monkeypatch)
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    with pytest.raises(ValidationError, match="prod requires STORAGE_BACKEND=s3"):
        Settings()


def test_prod_refuses_missing_s3_bucket(monkeypatch):
    set_prod_env(monkeypatch)
    monkeypatch.delenv("S3_BUCKET", raising=False)
    with pytest.raises(ValidationError, match="prod requires S3_BUCKET"):
        Settings()


def test_prod_refuses_local_auth_mode(monkeypatch):
    set_prod_env(monkeypatch)
    monkeypatch.setenv("AUTH_MODE", "local")
    with pytest.raises(ValidationError, match="prod requires AUTH_MODE=jwks"):
        Settings()


def test_prod_refuses_mock_tryon_provider(monkeypatch):
    set_prod_env(monkeypatch)
    monkeypatch.setenv("TRYON_PROVIDER", "mock")
    with pytest.raises(ValidationError, match="prod requires non-mock TRYON_PROVIDER"):
        Settings()


def test_prod_refuses_wildcard_cors(monkeypatch):
    set_prod_env(monkeypatch)
    monkeypatch.setenv("CORS_ORIGINS", '["*"]')
    with pytest.raises(ValidationError, match="wildcard CORS not allowed in prod"):
        Settings()
