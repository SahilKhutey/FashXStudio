from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from fashx.main import app
from fashx.security.deps import Principal, get_principal


def test_unauthenticated_pilot_endpoints_denied():
    client = TestClient(app)

    # /pilot/join without token
    r1 = client.post("/api/v1/pilot/join", json={"code": "ALPHA-1234"})
    assert r1.status_code == status.HTTP_401_UNAUTHORIZED

    # /pilot/feedback without token
    r2 = client.post("/api/v1/pilot/feedback", json={"kind": "bug", "message": "Crash on open"})
    assert r2.status_code == status.HTTP_401_UNAUTHORIZED

    # /pilot/surveys/pending without token
    r3 = client.get("/api/v1/pilot/surveys/pending")
    assert r3.status_code == status.HTTP_401_UNAUTHORIZED


def test_join_invalid_code_returns_404_not_found(monkeypatch):
    user_id = str(uuid4())
    fake_principal = Principal(user_id=user_id, subject="pilot_tester@example.com", roles=frozenset(["user"]))

    app.dependency_overrides[get_principal] = lambda: fake_principal
    client = TestClient(app)

    try:
        # Mock database session returning None for invite lookup
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        async def fake_get_db_session():
            yield mock_session

        monkeypatch.setattr("fashx.pilot.router.get_db_session", fake_get_db_session)

        resp = client.post("/api/v1/pilot/join", json={"code": "INVALID-CODE"})
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert resp.json().get("detail") == "Invalid or expired invite code"
    finally:
        app.dependency_overrides.pop(get_principal, None)


def test_survey_repeat_submission_returns_409_conflict(monkeypatch):
    user_id = str(uuid4())
    fake_principal = Principal(user_id=user_id, subject="pilot_tester@example.com", roles=frozenset(["user"]))

    app.dependency_overrides[get_principal] = lambda: fake_principal
    client = TestClient(app)

    try:
        mock_session = AsyncMock()
        # Mock check_stmt finding an existing response id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid4()
        mock_session.execute.return_value = mock_result

        async def fake_get_db_session():
            yield mock_session

        monkeypatch.setattr("fashx.pilot.router.get_db_session", fake_get_db_session)

        payload = {
            "survey_key": "tryon_first",
            "answers": {
                "looked_like_me": 4,
                "trust_for_buying": 4,
                "comment": "Good fit",
            },
        }

        resp = client.post("/api/v1/pilot/survey", json=payload)
        assert resp.status_code == status.HTTP_409_CONFLICT
        assert "already been submitted" in resp.json().get("detail", "")
    finally:
        app.dependency_overrides.pop(get_principal, None)
