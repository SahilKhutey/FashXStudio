import os
import pathlib
import sys
import time

import jwt
import pytest

os.environ.setdefault("ENV", "test")
os.environ.setdefault("AUTH_MODE", "local")
os.environ.setdefault("AUTH_JWT_SECRET", "test-secret-key-at-least-32-chars-long")
os.environ.setdefault("AUTH_ISSUER", "fashx-test")
os.environ.setdefault("AUTH_AUDIENCE", "fashx-api")

FROZEN_DIRS = {
    "inventory",
    "promotions",
    "cart",
    "checkout",
    "orders",
    "payments",
    "fulfillment",
    "returns",
}
FROZEN_FILES = {"test_cross_core.py"}

# Enable frozen routers if running all tests or specifically running frozen tests,
# unless "not frozen" is specified in the pytest marker argument.
if "not frozen" not in " ".join(sys.argv) and os.getenv("FASHX_ENABLE_FROZEN") is None:
    os.environ["FASHX_ENABLE_FROZEN"] = "1"


def pytest_collection_modifyitems(items):
    for item in items:
        p = pathlib.Path(str(item.fspath))
        if FROZEN_DIRS & set(p.parts) or p.name in FROZEN_FILES:
            item.add_marker(pytest.mark.frozen)


def make_token(
    sub: str = "user-a",
    iss: str = "fashx-test",
    aud: str = "fashx-api",
    exp_delta_seconds: int = 3600,
    secret: str = "test-secret-key-at-least-32-chars-long",
    alg: str = "HS256",
) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "iss": iss,
        "aud": aud,
        "exp": now + exp_delta_seconds,
        "iat": now,
    }
    return jwt.encode(payload, secret, algorithm=alg)


@pytest.fixture
def identity_repo():
    from fashx.security.identity import InMemoryIdentityRepo

    return InMemoryIdentityRepo()


@pytest.fixture
def anon_client(identity_repo):
    from fastapi.testclient import TestClient

    from fashx.main import create_app
    from fashx.security.deps import get_identity_repo

    app = create_app()
    app.dependency_overrides[get_identity_repo] = lambda: identity_repo
    with TestClient(app) as client:
        yield client


@pytest.fixture
def client_a(identity_repo):
    from fastapi.testclient import TestClient

    from fashx.main import create_app
    from fashx.security.deps import get_identity_repo

    app = create_app()
    app.dependency_overrides[get_identity_repo] = lambda: identity_repo
    token = make_token(sub="user-a")
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as client:
        yield client


@pytest.fixture
def client_b(identity_repo):
    from fastapi.testclient import TestClient

    from fashx.main import create_app
    from fashx.security.deps import get_identity_repo

    app = create_app()
    app.dependency_overrides[get_identity_repo] = lambda: identity_repo
    token = make_token(sub="user-b")
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as client:
        yield client


@pytest.fixture
def client_admin(identity_repo):
    import asyncio
    from fastapi.testclient import TestClient

    from fashx.main import create_app
    from fashx.security.deps import get_identity_repo

    asyncio.run(identity_repo.set_role("fashx-test", "user-admin", "admin"))
    app = create_app()
    app.dependency_overrides[get_identity_repo] = lambda: identity_repo
    token = make_token(sub="user-admin")
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as client:
        yield client
