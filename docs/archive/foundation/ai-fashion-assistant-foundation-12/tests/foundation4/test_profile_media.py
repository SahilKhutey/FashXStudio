from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from api.app.core.settings import get_settings
from api.app.main import app
from api.app.profile.router import get_media_service


class FakeMediaService:
    async def set_consent(self, user_id, *, data_type, granted):
        from types import SimpleNamespace
        return SimpleNamespace(granted=granted, updated_at=datetime.now(timezone.utc))

    async def create_photo_upload(self, user_id, *, photo_type, content_type, file_size_bytes):
        from types import SimpleNamespace
        photo_id = uuid4()
        return (
            SimpleNamespace(id=photo_id, status="upload_pending"),
            "https://upload.example.test/signed",
            datetime.now(timezone.utc) + timedelta(minutes=15),
        )

    async def complete_photo_upload(self, user_id, photo_id):
        from types import SimpleNamespace
        return (
            SimpleNamespace(id=photo_id, status="processing"),
            SimpleNamespace(id=uuid4()),
        )

    async def get_photo_status(self, user_id, photo_id):
        from types import SimpleNamespace
        return SimpleNamespace(
            id=photo_id,
            photo_type="tryon_reference",
            status="processing",
            reject_reason=None,
            version=1,
            created_at=datetime.now(timezone.utc),
        )

    async def create_scoped_media_url(self, *, photo_id, purpose, job_id):
        return "https://download.example.test/signed", datetime.now(timezone.utc) + timedelta(minutes=15)


def _token() -> str:
    return "foundation4-internal-token"


def setup_module():
    app.dependency_overrides[get_media_service] = lambda: FakeMediaService()


def teardown_module():
    app.dependency_overrides.pop(get_media_service, None)


def test_consent_contract():
    client = TestClient(app)
    user_id = uuid4()
    response = client.post(
        "/api/v1/profile/consent",
        headers={"X-User-ID": str(user_id)},
        json={"data_type": "body_photo", "granted": True},
    )
    assert response.status_code == 200
    assert response.json()["granted"] is True
    assert response.json()["data_type"] == "body_photo"


def test_photo_upload_returns_signed_url():
    client = TestClient(app)
    response = client.post(
        "/api/v1/profile/me/photos",
        headers={"X-User-ID": str(uuid4())},
        json={"photo_type": "tryon_reference", "content_type": "image/jpeg", "file_size_bytes": 1024},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "upload_pending"
    assert response.json()["upload_url"].startswith("https://")


def test_internal_media_access_fails_closed_without_token(monkeypatch):
    monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", _token())
    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post(
        "/api/v1/profile/internal/media-access",
        json={"photo_id": str(uuid4()), "purpose": "tryon", "job_id": str(uuid4())},
    )
    assert response.status_code == 403
    get_settings.cache_clear()


def test_internal_media_access_accepts_valid_token(monkeypatch):
    monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", _token())
    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post(
        "/api/v1/profile/internal/media-access",
        headers={"X-Internal-Service-Token": _token()},
        json={"photo_id": str(uuid4()), "purpose": "tryon", "job_id": str(uuid4())},
    )
    assert response.status_code == 200
    assert response.json()["access_url"].startswith("https://")
    get_settings.cache_clear()
