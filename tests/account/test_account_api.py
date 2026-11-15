
import pytest
from fastapi.testclient import TestClient

from fashx.main import app
from tests.conftest import make_token


@pytest.fixture
def auth_headers():
    token = make_token(sub="shopper-api-test-sub")
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_account_endpoints_return_401():
    client = TestClient(app)
    assert client.get("/api/v1/account/me").status_code == 401
    assert client.post("/api/v1/account/provision", json={}).status_code == 401
    assert client.post("/api/v1/account/email-change", json={"new_email": "new@fashx.com"}).status_code == 401
    assert client.post("/api/v1/account/disable", json={}).status_code == 401
    assert client.post("/api/v1/account/deletion-request", json={}).status_code == 401
    assert client.get("/api/v1/account/deletion-status").status_code == 401
    assert client.post("/api/v1/account/sessions/revoke-all").status_code == 401


def test_provision_and_get_me_flow(auth_headers):
    client = TestClient(app, headers=auth_headers)

    # 1. Provision account
    prov_res = client.post(
        "/api/v1/account/provision",
        json={"email": "shopper.api@example.com", "email_verified": True},
    )
    assert prov_res.status_code == 200
    prov_data = prov_res.json()
    assert prov_data["email_normalized"] == "shopper.api@example.com"
    assert prov_data["status"] == "ACTIVE"

    # 2. Get Me
    me_res = client.get("/api/v1/account/me")
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user_id"] == prov_data["user_id"]
    assert me_data["email_normalized"] == "shopper.api@example.com"
    assert me_data["email_verified"] is True
    assert me_data["status"] == "ACTIVE"


def test_email_change_workflow(auth_headers):
    client = TestClient(app, headers=auth_headers)

    # Provision initial
    client.post(
        "/api/v1/account/provision",
        json={"email": "original@example.com", "email_verified": True},
    )

    # Request email change
    req_res = client.post(
        "/api/v1/account/email-change",
        json={"new_email": "updated@example.com"},
    )
    assert req_res.status_code == 200
    assert req_res.json()["status"] == "verification_sent"

    # Confirm email change with valid code
    confirm_res = client.post(
        "/api/v1/account/email-change/confirm",
        json={"new_email": "updated@example.com", "confirmation_code": "123456"},
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["email_normalized"] == "updated@example.com"

    # Verify Get Me reflects updated email
    me_res = client.get("/api/v1/account/me")
    assert me_res.status_code == 200
    assert me_res.json()["email_normalized"] == "updated@example.com"


def test_disable_account_flow(auth_headers):
    client = TestClient(app, headers=auth_headers)

    # Provision
    client.post(
        "/api/v1/account/provision",
        json={"email": "to_disable@example.com", "email_verified": True},
    )

    # Disable
    dis_res = client.post(
        "/api/v1/account/disable",
        json={"reason": "User requested temporary hold"},
    )
    assert dis_res.status_code == 200
    assert dis_res.json()["status"] == "DISABLED"


def test_revoke_all_sessions_endpoint(auth_headers):
    client = TestClient(app, headers=auth_headers)

    # Provision
    client.post(
        "/api/v1/account/provision",
        json={"email": "session_user@example.com", "email_verified": True},
    )

    # Revoke sessions
    rev_res = client.post("/api/v1/account/sessions/revoke-all")
    assert rev_res.status_code == 200
    assert "revoked_sessions_count" in rev_res.json()
