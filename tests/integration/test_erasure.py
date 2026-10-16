from uuid import uuid4

import pytest
from sqlalchemy import text

from database.models import Base
from fashx.application.erasure import (
    ACCOUNT_TABLES,
    ANONYMIZE_TABLES,
    BIOMETRIC_TABLES,
    RETAINED_MINIMAL,
    erase_account,
    erase_biometrics,
)
from fashx.infrastructure.storage.local import LocalStorage


def test_every_model_table_is_classified():
    """Verify that every mapped table in Base with a user_id column is classified."""
    model_user_tables = set()
    for mapper in Base.registry.mappers:
        table = mapper.local_table
        for col in table.columns:
            if col.name == "user_id":
                model_user_tables.add(table.name)

    unknown = (
        model_user_tables
        - set(BIOMETRIC_TABLES)
        - set(ACCOUNT_TABLES)
        - set(ANONYMIZE_TABLES)
        - set(RETAINED_MINIMAL)
        - {"auth_identities"}
    )
    assert not unknown, f"Classify these tables for erasure: {unknown}"


@pytest.mark.db
def test_every_user_table_is_classified(db_engine):
    """Database-level test verifying every public table with user_id is classified."""
    with db_engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    "select table_name from information_schema.columns "
                    "where table_schema='public' and column_name='user_id'"
                )
            )
            .scalars()
            .all()
        )
    unknown = (
        set(rows)
        - set(BIOMETRIC_TABLES)
        - set(ACCOUNT_TABLES)
        - set(ANONYMIZE_TABLES)
        - set(RETAINED_MINIMAL)
        - {"auth_identities"}
    )
    assert not unknown, f"Classify these tables for erasure: {unknown}"


def test_erasure_pipeline_local_storage(tmp_path):
    """Verifies that erase_biometrics and erase_account purge user files and queues tasks."""
    user_id = uuid4()
    storage = LocalStorage(tmp_path)

    # Seed storage objects
    p1 = f"u/{user_id}/photos/{uuid4()}.jpg"
    p2 = f"u/{user_id}/photos/{uuid4()}.jpg"
    t1 = f"u/{user_id}/tryon/{uuid4()}.jpg"
    other_u = uuid4()
    p_other = f"u/{other_u}/photos/{uuid4()}.jpg"

    storage.put(p1, b"photo1", "image/jpeg")
    storage.put(p2, b"photo2", "image/jpeg")
    storage.put(t1, b"tryon1", "image/jpeg")
    storage.put(p_other, b"other_photo", "image/jpeg")

    assert len(storage.list_prefix(f"u/{user_id}/")) == 3
    assert storage.exists(p_other)

    class MockUoW:
        def __init__(self):
            self.session = None
            self.outbox_messages = []

        class MockOutbox:
            def __init__(self, parent):
                self.parent = parent

            async def add(self, msg):
                self.parent.outbox_messages.append(msg)

        @property
        def outbox(self):
            return self.MockOutbox(self)

    import asyncio

    uow = MockUoW()

    # Run erase_biometrics
    asyncio.run(erase_biometrics(uow, user_id, storage=storage))

    # Assert storage prefix is wiped for user, but other user is intact
    assert storage.list_prefix(f"u/{user_id}/") == []
    assert storage.exists(p_other)
    assert len(uow.outbox_messages) == 1
    assert uow.outbox_messages[0].event.prefix == f"u/{user_id}/"
    assert uow.outbox_messages[0].event.event_type == "StoragePurgeRequested"

    # Seed more files and run erase_account
    storage.put(p1, b"photo1_new", "image/jpeg")
    uow_acc = MockUoW()
    asyncio.run(erase_account(uow_acc, user_id, storage=storage))
    assert storage.list_prefix(f"u/{user_id}/") == []
    assert storage.exists(p_other)
    assert len(uow_acc.outbox_messages) >= 1


def test_delete_me_api_endpoint(client_a):
    """Verifies DELETE /api/v1/me endpoint returns HTTP 202 queued."""
    from fashx.api.v1.me import get_profile_uow

    class DummyUoW:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def commit(self):
            pass

    client_a.app.dependency_overrides[get_profile_uow] = lambda: DummyUoW()
    try:
        res = client_a.delete("/api/v1/me")
        assert res.status_code == 202
        data = res.json()
        assert data["status"] == "queued"
        assert "user_id" in data
    finally:
        client_a.app.dependency_overrides.pop(get_profile_uow, None)


@pytest.mark.db
def test_revoke_leaves_zero_biometric_residue(db, tmp_path):
    """Gate G4 test verifying complete removal of biometric rows and storage files."""
    user_id = uuid4()
    storage = LocalStorage(tmp_path)
    p_key = f"u/{user_id}/photos/portrait.jpg"
    t_key = f"u/{user_id}/tryon/job1.jpg"

    storage.put(p_key, b"portrait_data", "image/jpeg")
    storage.put(t_key, b"tryon_data", "image/jpeg")
    assert len(storage.list_prefix(f"u/{user_id}/")) == 2

    class DirectUoW:
        def __init__(self, session):
            self.session = session
            self.photos = None
            self.body_profiles = None

    import asyncio

    asyncio.run(erase_biometrics(DirectUoW(db), user_id, storage=storage))

    # All storage keys for user wiped
    assert storage.list_prefix(f"u/{user_id}/") == []
    for t in BIOMETRIC_TABLES:
        cnt = db.execute(text(f'select count(*) from "{t}" where user_id = :u'), {"u": user_id}).scalar()
        assert cnt == 0


@pytest.mark.db
def test_garments_sizes_in_stock_gin_index_exists(db_engine):
    """Assert that canonical_garments has the GIN index on sizes_in_stock in PostgreSQL."""
    with db_engine.connect() as conn:
        res = conn.execute(text(
            "SELECT indexname, indexdef FROM pg_indexes "
            "WHERE tablename = 'canonical_garments' AND indexdef LIKE '%gin%'"
        )).fetchall()
        assert any("sizes_in_stock" in r[1] for r in res), "Expected GIN index on sizes_in_stock"


@pytest.mark.db
def test_erase_account_leaves_zero_residue_on_postgres(db, tmp_path):
    """End-to-end erasure test on real Postgres: seed user data across tables, erase, assert zero rows."""
    import asyncio
    user_id = uuid4()
    storage = LocalStorage(tmp_path)
    p_key = f"u/{user_id}/photos/portrait.jpg"
    storage.put(p_key, b"portrait_data", "image/jpeg")

    # Seed user and user-keyed rows
    db.execute(text('INSERT INTO "users" (id, created_at, updated_at) VALUES (:u, now(), now())'), {"u": user_id})
    db.execute(
        text('INSERT INTO "consent_records" (user_id, data_type, granted, policy_version, is_18_or_older, updated_at) VALUES (:u, :dt, true, :pv, true, now())'),
        {"u": user_id, "dt": "terms_and_privacy", "pv": "2026.1"},
    )
    db.execute(
        text('INSERT INTO "user_preferences" (user_id, categories, colors_favored, colors_avoided, updated_at) VALUES (:u, :cats, :fav, :av, now())'),
        {"u": user_id, "cats": "[]", "fav": "[]", "av": "[]"},
    )
    db.flush()

    class DirectUoW:
        def __init__(self, session):
            self.session = session

    asyncio.run(erase_account(DirectUoW(db), user_id, storage=storage))
    db.flush()

    assert storage.list_prefix(f"u/{user_id}/") == []
    for t in BIOMETRIC_TABLES:
        cnt = db.execute(text(f'select count(*) from "{t}" where user_id = :u'), {"u": user_id}).scalar()
        assert cnt == 0, f"Expected 0 rows in biometric table {t}"
    for t in ACCOUNT_TABLES:
        if t == "users":
            continue
        cnt = db.execute(text(f'select count(*) from "{t}" where user_id = :u'), {"u": user_id}).scalar()
        assert cnt == 0, f"Expected 0 rows in account table {t}"
    # Canonical user row deleted
    user_cnt = db.execute(text('select count(*) from "users" where id = :u'), {"u": user_id}).scalar()
    assert user_cnt == 0, "Expected user row to be deleted"
