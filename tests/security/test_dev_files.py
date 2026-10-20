from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi.testclient import TestClient

from fashx.core.dependencies import get_storage
from fashx.core.settings import Settings
from fashx.infrastructure.storage.local import LocalStorage
from fashx.main import create_app


def test_dev_files_serves_valid_signed_url(tmp_path: Path) -> None:
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    test_file = storage_dir / "test_image.jpg"
    test_file.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIFdummy-jpeg-data")

    settings = Settings(
        env="dev",
        storage_backend="local",
        local_storage_dir=str(storage_dir),
        enable_b2b=False,
        enable_frozen=False,
    )
    app = create_app(settings)
    storage = LocalStorage(root_dir=storage_dir)
    app.dependency_overrides[get_storage] = lambda: storage
    client = TestClient(app)

    signed_url = storage.signed_get_url("test_image.jpg", ttl_s=60)
    path_and_query = signed_url.split("http://127.0.0.1:8000")[-1]

    response = client.get(path_and_query)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content == b"\xff\xd8\xff\xe0\x00\x10JFIFdummy-jpeg-data"


def test_dev_files_denies_tampered_signature(tmp_path: Path) -> None:
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    test_file = storage_dir / "sample.png"
    test_file.write_bytes(b"dummy-png")

    settings = Settings(
        env="dev",
        storage_backend="local",
        local_storage_dir=str(storage_dir),
    )
    app = create_app(settings)
    storage = LocalStorage(root_dir=storage_dir)
    app.dependency_overrides[get_storage] = lambda: storage
    client = TestClient(app)

    # Missing sig
    res1 = client.get("/dev-files/sample.png")
    assert res1.status_code == 403
    assert "Invalid or expired signature" in res1.json()["detail"]

    # Tampered sig
    exp = int(time.time()) + 300
    res2 = client.get(f"/dev-files/sample.png?exp={exp}&sig=tampered_bad_sig")
    assert res2.status_code == 403
    assert "Invalid or expired signature" in res2.json()["detail"]


def test_dev_files_denies_expired_signature(tmp_path: Path) -> None:
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    test_file = storage_dir / "sample.webp"
    test_file.write_bytes(b"dummy-webp")

    settings = Settings(
        env="dev",
        storage_backend="local",
        local_storage_dir=str(storage_dir),
    )
    app = create_app(settings)
    storage = LocalStorage(root_dir=storage_dir)
    app.dependency_overrides[get_storage] = lambda: storage
    client = TestClient(app)

    exp = int(time.time()) - 10
    sig = storage._sign("sample.webp", exp)

    res = client.get(f"/dev-files/sample.webp?exp={exp}&sig={sig}")
    assert res.status_code == 403
    assert "Invalid or expired signature" in res.json()["detail"]


def test_dev_files_prevents_path_traversal(tmp_path: Path) -> None:
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    secret_file = tmp_path / "secret.jpg"
    secret_file.write_bytes(b"secret-data")

    settings = Settings(
        env="dev",
        storage_backend="local",
        local_storage_dir=str(storage_dir),
    )
    app = create_app(settings)
    storage = LocalStorage(root_dir=storage_dir)
    app.dependency_overrides[get_storage] = lambda: storage
    client = TestClient(app)

    exp = int(time.time()) + 300

    # Attempt path traversal outside storage_dir with valid signature for that path
    traversal_key = "../secret.jpg"
    sig = storage._sign(traversal_key, exp)

    res = client.get(f"/dev-files/{traversal_key}?exp={exp}&sig={sig}")
    assert res.status_code == 404

    # Disallowed extension (.txt)
    txt_file = storage_dir / "notes.txt"
    txt_file.write_text("sensitive")
    sig_txt = storage._sign("notes.txt", exp)
    res_txt = client.get(f"/dev-files/notes.txt?exp={exp}&sig={sig_txt}")
    assert res_txt.status_code == 404


def test_dev_files_not_mounted_in_production(tmp_path: Path) -> None:
    orig_env = os.environ.get("ENV")
    try:
        os.environ["ENV"] = "prod"
        prod_settings = Settings(
            env="prod",
            repo_backend="sql",
            storage_backend="s3",
            enable_b2b=False,
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
        app = create_app(prod_settings)
        client = TestClient(app)

        res = client.get("/dev-files/photo.jpg?exp=9999999999&sig=dummy")
        assert res.status_code == 404
    finally:
        if orig_env is not None:
            os.environ["ENV"] = orig_env
        else:
            os.environ.pop("ENV", None)
