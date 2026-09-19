from fastapi.testclient import TestClient
from uuid import uuid4

from api.app.main import app
from api.app.profile.router import get_media_service


class FakeGuidanceService:
    async def get_capture_guidance(self, user_id, photo_id):
        return {
            "photo_id": photo_id,
            "state": "retry",
            "ready_for_tryon": False,
            "title": "Step closer",
            "message": "Your body is too small in the frame for reliable try-on alignment.",
            "tips": ["Face the camera directly."],
            "retryable": True,
            "quality_score": 0.41,
            "reasons": ["subject_small_in_frame"],
        }


def setup_module():
    app.dependency_overrides[get_media_service] = lambda: FakeGuidanceService()


def teardown_module():
    app.dependency_overrides.pop(get_media_service, None)


def test_capture_guidance_contract():
    client = TestClient(app)
    response = client.get(
        f"/api/v1/profile/me/photos/{uuid4()}/guidance",
        headers={"X-User-ID": str(uuid4())},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "retry"
    assert payload["retryable"] is True
    assert "subject_small_in_frame" in payload["reasons"]
