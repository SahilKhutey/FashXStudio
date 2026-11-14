from unittest.mock import patch

from pydantic import SecretStr

from fashx.core.dependencies import get_storage
from fashx.core.settings import Settings
from fashx.infrastructure.storage.s3 import S3Storage


def test_s3_storage_initializes_with_none_credentials_for_iam():
    with patch("boto3.client") as mock_client:
        storage = S3Storage(
            bucket="fashx-prod-media-private",
            region="ap-south-1",
            key_id=None,
            secret=None,
        )
        assert storage._b == "fashx-prod-media-private"
        mock_client.assert_called_once()
        _, kwargs = mock_client.call_args
        assert kwargs["aws_access_key_id"] is None
        assert kwargs["aws_secret_access_key"] is None


def test_get_storage_passes_none_when_iam_role_enabled():
    mock_settings = Settings(
        ENV="dev",
        APP_ENV="development",
        REPO_BACKEND="sql",
        STORAGE_BACKEND="s3",
        S3_BUCKET="fashx-dev-media-private",
        S3_USE_IAM_ROLE=True,
        S3_ACCESS_KEY_ID=SecretStr("static-key-ignored"),
        S3_SECRET_ACCESS_KEY=SecretStr("static-secret-ignored"),
        AUTH_MODE="jwks",
        AUTH_JWKS_URL="https://auth.dev.example.com/.well-known/jwks.json",
        CORS_ORIGINS=["http://localhost:8081"],
    )

    with patch("fashx.core.settings.get_settings", return_value=mock_settings):
        with patch("boto3.client") as mock_client:
            storage = get_storage()
            assert isinstance(storage, S3Storage)
            assert storage._b == "fashx-dev-media-private"
            _, kwargs = mock_client.call_args
            assert kwargs["aws_access_key_id"] is None
            assert kwargs["aws_secret_access_key"] is None


def test_get_storage_passes_credentials_when_iam_role_disabled():
    mock_settings = Settings(
        ENV="dev",
        APP_ENV="development",
        REPO_BACKEND="sql",
        STORAGE_BACKEND="s3",
        S3_BUCKET="fashx-dev-media-private",
        S3_USE_IAM_ROLE=False,
        S3_ACCESS_KEY_ID=SecretStr("my-access-key"),
        S3_SECRET_ACCESS_KEY=SecretStr("my-secret-key"),
        AUTH_MODE="local",
        AUTH_JWT_SECRET="local-secret-at-least-32-chars-long",
    )

    with patch("fashx.core.settings.get_settings", return_value=mock_settings):
        with patch("boto3.client") as mock_client:
            storage = get_storage()
            assert isinstance(storage, S3Storage)
            assert storage._b == "fashx-dev-media-private"
            _, kwargs = mock_client.call_args
            assert kwargs["aws_access_key_id"] == "my-access-key"
            assert kwargs["aws_secret_access_key"] == "my-secret-key"
