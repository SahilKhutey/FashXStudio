import os
import pathlib
import sys
import time

import jwt
import pytest
from fastapi.testclient import TestClient

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


def pytest_configure(config):
    config.addinivalue_line("markers", "db: needs a real Postgres (TEST_DATABASE_URL)")


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


_orig_testclient_init = TestClient.__init__


def _patched_testclient_init(self, app, *args, **kwargs):
    headers = kwargs.get("headers")
    if headers is None:
        headers = {}
        kwargs["headers"] = headers
    if "Authorization" not in headers:
        import inspect

        frame = inspect.currentframe()
        in_security_test = False
        while frame:
            filename = frame.f_code.co_filename.replace("\\", "/")
            if "tests/security" in filename:
                in_security_test = True
                break
            frame = frame.f_back
        if not in_security_test:
            headers["Authorization"] = f"Bearer {make_token('test-user')}"
    _orig_testclient_init(self, app, *args, **kwargs)


TestClient.__init__ = _patched_testclient_init


@pytest.fixture(autouse=True)
def setup_test_identity_override():
    from fashx.main import app as main_app
    from fashx.security.deps import get_identity_repo
    from fashx.security.identity import InMemoryIdentityRepo

    shared_repo = InMemoryIdentityRepo()
    main_app.dependency_overrides[get_identity_repo] = lambda: shared_repo
    yield
    main_app.dependency_overrides.pop(get_identity_repo, None)


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


@pytest.fixture(scope="session")
def db_engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set")
    assert url.rsplit("/", 1)[-1].endswith("_test"), "refusing to run against a non-test database"
    os.environ["DATABASE_URL"] = url

    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text

    sync_url = url.replace("+asyncpg", "").replace("+aiosqlite", "")
    engine = create_engine(sync_url, future=True)
    with engine.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE"))
        c.execute(text("CREATE SCHEMA public"))
        c.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    command.upgrade(Config("alembic.ini"), "head")
    yield engine
    engine.dispose()


@pytest.fixture
def db(db_engine):
    """One test = one rolled-back transaction. Repos may commit; that only releases a SAVEPOINT."""
    from sqlalchemy.orm import Session

    conn = db_engine.connect()
    trans = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    trans.rollback()
    conn.close()


@pytest.fixture
def committed_db(db_engine):
    """For concurrency tests that need real commits across connections. Truncates afterwards."""
    from sqlalchemy import text

    yield db_engine
    with db_engine.begin() as c:
        names = [
            r[0]
            for r in c.execute(
                text(
                    "select tablename from pg_tables where schemaname='public' and tablename <> 'alembic_version'"
                )
            )
        ]
        if names:
            c.execute(
                text("TRUNCATE " + ",".join(f'"{n}"' for n in names) + " RESTART IDENTITY CASCADE")
            )
