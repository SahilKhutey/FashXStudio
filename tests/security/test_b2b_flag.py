from __future__ import annotations

import pytest

from fashx.core.settings import Settings
from fashx.main import create_app


def test_b2b_routes_absent_by_default() -> None:
    settings = Settings(enable_b2b=False, enable_frozen=False)
    app = create_app(settings)
    paths = app.openapi()["paths"]

    b2b_paths = [p for p in paths if any(k in p for k in ("/widget", "/tenant", "/b2b"))]
    assert b2b_paths == [], f"Expected zero B2B paths when enable_b2b=False, found: {b2b_paths}"


def test_b2b_routes_present_when_flag_enabled() -> None:
    settings = Settings(enable_b2b=True, enable_frozen=False)
    app = create_app(settings)
    paths = app.openapi()["paths"]

    b2b_paths = [p for p in paths if any(k in p for k in ("/widget", "/tenant", "/b2b"))]
    assert len(b2b_paths) > 0, "Expected B2B routes to be mounted when enable_b2b=True"
    assert "/widget/v1/session" in paths
    assert "/widget/v1/tryon" in paths


def test_b2b_flag_forbidden_in_production() -> None:
    with pytest.raises(ValueError, match="ENABLE_B2B must be false in prod for MVP"):
        Settings(
            env="prod",
            repo_backend="sql",
            storage_backend="s3",
            enable_b2b=True,
            enable_frozen=False,
            s3_bucket="fashx-prod-bucket",
            s3_use_iam_role=True,
            auth_mode="jwks",
            auth_jwks_url="https://auth.example.com/.well-known/jwks.json",
            tryon_provider="fashn_api",
            fashn_api_key="test-key-mock",
            privacy_url="https://fashx.com/privacy",
            terms_url="https://fashx.com/terms",
        )
