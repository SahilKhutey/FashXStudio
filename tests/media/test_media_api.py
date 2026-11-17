from __future__ import annotations

import io
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from fashx.core.dependencies import get_storage
from fashx.main import app
from tests.conftest import make_token

pytestmark = [pytest.mark.db]


def make_test_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (500, 500), (70, 130, 180))
    draw = ImageDraw.Draw(img)
    for i in range(0, 500, 20):
        draw.line([(i, 0), (500 - i, 500)], fill=(i % 255, 100, 200), width=2)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def user_a_headers():
    token = make_token(sub="00000000-0000-0000-0000-000000000001")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_b_headers():
    token = make_token(sub="00000000-0000-0000-0000-000000000002")
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_media_endpoints():
    client = TestClient(app, headers={"Authorization": ""})
    random_id = str(uuid4())
    assert client.post("/api/v1/media/uploads", json={}).status_code == 401
    assert client.get(f"/api/v1/media/uploads/{random_id}").status_code == 401
    assert client.post(f"/api/v1/media/uploads/{random_id}/complete").status_code == 401
    assert client.get(f"/api/v1/media/{random_id}").status_code == 401
    assert client.post(f"/api/v1/media/{random_id}/access-url").status_code == 401
    assert client.delete(f"/api/v1/media/{random_id}").status_code == 401


def test_initiate_upload_success(user_a_headers):
    client = TestClient(app, headers=user_a_headers)
    jpeg_bytes = make_test_jpeg_bytes()

    res = client.post(
        "/api/v1/media/uploads",
        json={
            "purpose": "VTO_PERSONAL_PHOTO",
            "filename": "portrait.jpg",
            "content_type": "image/jpeg",
            "declared_size_bytes": len(jpeg_bytes),
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "upload_id" in data
    assert "image_id" in data
    assert data["method"] == "PUT"
    assert data["status"] == "PENDING_UPLOAD"
    assert data["required_headers"] == {"Content-Type": "image/jpeg"}
    assert "upload_url" in data
    assert len(data["upload_url"]) > 0


def test_concurrency_and_rate_limiting(user_a_headers):
    client = TestClient(app, headers=user_a_headers)
    jpeg_bytes = make_test_jpeg_bytes()
    storage = get_storage()
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    # 1. Test concurrency limit: 3 pending uploads allowed, 4th rejected
    upload_responses = []
    for i in range(3):
        res = client.post(
            "/api/v1/media/uploads",
            json={
                "purpose": "PROFILE_PHOTO",
                "filename": f"profile_{i}.jpg",
                "content_type": "image/jpeg",
                "declared_size_bytes": len(jpeg_bytes),
            },
        )
        assert res.status_code == 201
        upload_responses.append(res.json())

    # 4th concurrent pending upload must fail with 429 concurrent_uploads_exceeded
    res_concurrent = client.post(
        "/api/v1/media/uploads",
        json={
            "purpose": "PROFILE_PHOTO",
            "filename": "profile_concurrent.jpg",
            "content_type": "image/jpeg",
            "declared_size_bytes": len(jpeg_bytes),
        },
    )
    assert res_concurrent.status_code == 429
    assert res_concurrent.json()["error"]["code"] == "concurrent_uploads_exceeded"

    # Complete the 3 pending uploads so concurrency frees up
    for upload_data in upload_responses:
        put_res = client.put(
            upload_data["upload_url"],
            content=jpeg_bytes,
            headers=upload_data["required_headers"],
        )
        assert put_res.status_code == 200
        c_res = client.post(f"/api/v1/media/uploads/{upload_data['upload_id']}/complete")
        assert c_res.status_code == 200

    # User now has 3 completed uploads within 15 mins. Let's add 2 more to reach 5 total:
    for i in range(3, 5):
        res = client.post(
            "/api/v1/media/uploads",
            json={
                "purpose": "PROFILE_PHOTO",
                "filename": f"profile_{i}.jpg",
                "content_type": "image/jpeg",
                "declared_size_bytes": len(jpeg_bytes),
            },
        )
        assert res.status_code == 201
        upload_data = res.json()
        put_res = client.put(
            upload_data["upload_url"],
            content=jpeg_bytes,
            headers=upload_data["required_headers"],
        )
        assert put_res.status_code == 200
        c_res = client.post(f"/api/v1/media/uploads/{upload_data['upload_id']}/complete")
        assert c_res.status_code == 200

    # 6th upload in 15 min must trigger rate limit
    res_rate = client.post(
        "/api/v1/media/uploads",
        json={
            "purpose": "PROFILE_PHOTO",
            "filename": "profile_excess.jpg",
            "content_type": "image/jpeg",
            "declared_size_bytes": len(jpeg_bytes),
        },
    )
    assert res_rate.status_code == 429
    assert res_rate.json()["error"]["code"] == "upload_rate_limited"


def test_complete_upload_workflow_and_metadata(user_b_headers):
    client = TestClient(app, headers=user_b_headers)
    jpeg_bytes = make_test_jpeg_bytes()
    storage = get_storage()

    # 1. Initiate upload
    init_res = client.post(
        "/api/v1/media/uploads",
        json={
            "purpose": "VTO_PERSONAL_PHOTO",
            "filename": "fitting_photo.jpg",
            "content_type": "image/jpeg",
            "declared_size_bytes": len(jpeg_bytes),
        },
    )
    assert init_res.status_code == 201
    init_data = init_res.json()
    upload_id = init_data["upload_id"]
    image_id = init_data["image_id"]

    # 2. Upload via presigned upload URL
    put_res = client.put(
        init_data["upload_url"],
        content=jpeg_bytes,
        headers=init_data["required_headers"],
    )
    assert put_res.status_code == 200

    # 3. Complete upload
    comp_res = client.post(f"/api/v1/media/uploads/{upload_id}/complete")
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["status"] == "AVAILABLE"
    assert comp_data["image_id"] == image_id

    # 4. Check that quarantine key was purged
    q_key = init_data["upload_url"].split("?")[0].replace("/dev-files/", "")
    assert not storage.exists(q_key)

    # 5. Check metadata
    meta_res = client.get(f"/api/v1/media/{image_id}")
    assert meta_res.status_code == 200
    meta_data = meta_res.json()
    assert meta_data["id"] == image_id
    assert meta_data["status"] == "AVAILABLE"
    assert meta_data["content_type"] == "image/webp"
    assert meta_data["width"] == 500
    assert meta_data["height"] == 500
    assert len(meta_data["sha256_normalized"]) == 64

    # 6. Check access URL generation
    access_res = client.post(f"/api/v1/media/{image_id}/access-url")
    assert access_res.status_code == 200
    access_data = access_res.json()
    assert access_data["image_id"] == image_id
    assert "url" in access_data
    assert access_data["expires_in_seconds"] == 60


def test_cross_user_isolation(user_a_headers, user_b_headers):
    client_a = TestClient(app, headers=user_a_headers)
    client_b = TestClient(app, headers=user_b_headers)
    jpeg_bytes = make_test_jpeg_bytes()
    storage = get_storage()

    # User A initiates & completes an image
    init_res = client_a.post(
        "/api/v1/media/uploads",
        json={
            "purpose": "VTO_PERSONAL_PHOTO",
            "filename": "user_a_photo.jpg",
            "content_type": "image/jpeg",
            "declared_size_bytes": len(jpeg_bytes),
        },
    )
    assert init_res.status_code == 201
    init_data = init_res.json()
    upload_id = init_data["upload_id"]
    image_id = init_data["image_id"]

    put_res = client_a.put(
        init_data["upload_url"],
        content=jpeg_bytes,
        headers=init_data["required_headers"],
    )
    assert put_res.status_code == 200

    comp_res = client_a.post(f"/api/v1/media/uploads/{upload_id}/complete")
    assert comp_res.status_code == 200

    # User B attempts to access User A's image: must strictly return 404
    assert client_b.get(f"/api/v1/media/{image_id}").status_code == 404
    assert client_b.post(f"/api/v1/media/{image_id}/access-url").status_code == 404
    assert client_b.delete(f"/api/v1/media/{image_id}").status_code == 404
    assert client_b.get(f"/api/v1/media/uploads/{upload_id}").status_code == 404
    assert client_b.post(f"/api/v1/media/uploads/{upload_id}/complete").status_code == 404


def test_delete_media_lifecycle(user_b_headers):
    client = TestClient(app, headers=user_b_headers)
    jpeg_bytes = make_test_jpeg_bytes()
    storage = get_storage()

    # Initiate & complete image
    init_res = client.post(
        "/api/v1/media/uploads",
        json={
            "purpose": "PROFILE_PHOTO",
            "filename": "to_be_deleted.jpg",
            "content_type": "image/jpeg",
            "declared_size_bytes": len(jpeg_bytes),
        },
    )
    assert init_res.status_code == 201
    init_data = init_res.json()
    upload_id = init_data["upload_id"]
    image_id = init_data["image_id"]

    put_res = client.put(
        init_data["upload_url"],
        content=jpeg_bytes,
        headers=init_data["required_headers"],
    )
    assert put_res.status_code == 200

    c_res = client.post(f"/api/v1/media/uploads/{upload_id}/complete")
    assert c_res.status_code == 200

    # Verify image exists
    assert client.get(f"/api/v1/media/{image_id}").status_code == 200

    # Delete image
    del_res = client.delete(f"/api/v1/media/{image_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETION_PENDING"

    # Subsequent GET or access-url must return 404
    assert client.get(f"/api/v1/media/{image_id}").status_code == 404
    assert client.post(f"/api/v1/media/{image_id}/access-url").status_code == 404
