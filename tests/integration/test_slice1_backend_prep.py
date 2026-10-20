from __future__ import annotations

import io
import json
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from fashx.core.settings import get_settings
from fashx.main import app
from schemas.common.enums import PhotoStatus
from scripts.export_reject_reasons import get_reject_reasons


def make_valid_photo_bytes(w: int = 600, h: int = 800) -> bytes:
    img = Image.new("RGB", (w, h), (140, 120, 105))
    # Add contrast
    for x in range(w // 2):
        for y in range(h):
            img.putpixel((x, y), (100, 80, 65))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_config_endpoint_returns_consent_version_and_legal() -> None:
    client = TestClient(app)
    res = client.get("/api/v1/config")
    assert res.status_code == 200
    data = res.json()
    assert "consent_version" in data
    assert data["consent_version"] == get_settings().consent_version
    assert "legal" in data
    assert "privacy_url" in data["legal"]
    assert "terms_url" in data["legal"]


def test_reject_reasons_json_matches_enum_stale_file_check() -> None:
    json_path = Path("mobile/src/api/reject-reasons.json")
    assert json_path.exists(), "mobile/src/api/reject-reasons.json does not exist. Run scripts/export_reject_reasons.py."
    in_file = json.loads(json_path.read_text(encoding="utf-8"))
    expected = get_reject_reasons()
    assert in_file == expected, "mobile/src/api/reject-reasons.json is stale! Run python scripts/export_reject_reasons.py."


@pytest.mark.asyncio
async def test_photo_upload_without_consent_returns_403_consent_required() -> None:
    client = TestClient(app)
    # Get current user
    me_res = client.get("/api/v1/me")
    assert me_res.status_code == 200
    user_id_str = me_res.json()["user_id"]
    user_id = UUID(user_id_str)

    from database.models.identity import User
    from fashx.profile.router import get_profile_uow

    uow_factory = app.dependency_overrides.get(get_profile_uow, get_profile_uow)
    uow = uow_factory()
    async with uow:
        existing = await uow.users.get_by_id(user_id)
        if not existing:
            uow.users.add(User(id=user_id))
            await uow.commit()

    photo_bytes = make_valid_photo_bytes()

    # Upload via multipart form without consent
    res = client.post(
        f"/api/v1/profile/{user_id}/photos",
        files={"file": ("photo.jpg", photo_bytes, "image/jpeg")},
    )
    assert res.status_code == 403
    err = res.json()
    assert err["error"]["code"] == "consent_required"


@pytest.mark.asyncio
async def test_photo_upload_multipart_form_with_consent_succeeds() -> None:
    client = TestClient(app)
    me_res = client.get("/api/v1/me")
    user_id_str = me_res.json()["user_id"]
    user_id = UUID(user_id_str)

    from database.models.identity import User
    from fashx.profile.router import get_profile_uow

    uow_factory = app.dependency_overrides.get(get_profile_uow, get_profile_uow)
    uow = uow_factory()
    async with uow:
        existing = await uow.users.get_by_id(user_id)
        if not existing:
            uow.users.add(User(id=user_id))
            await uow.commit()

    # Grant consent
    consent_res = client.post(
        f"/api/v1/profile/{user_id}/consent",
        json={
            "consent_version": "2026.1",
            "is_18_or_older": True,
            "accepts_terms": True,
            "accepts_body_photo": True,
        },
    )
    assert consent_res.status_code == 201

    photo_bytes = make_valid_photo_bytes()

    # Upload via multipart
    res = client.post(
        f"/api/v1/profile/{user_id}/photos",
        files={"file": ("photo.jpg", photo_bytes, "image/jpeg")},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == PhotoStatus.ACCEPTED.value
    assert data["reject_reason"] is None
    assert data["storage_key"] is not None
