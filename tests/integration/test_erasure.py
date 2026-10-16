from uuid import uuid4

import pytest
from sqlalchemy import text

from database.models import Base
from fashx.application.erasure import (
    ACCOUNT_TABLES,
    ANONYMIZE_TABLES,
    BIOMETRIC_TABLES,
    CORE_AUTH,
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
        - set(CORE_AUTH)
    )
    assert not unknown, f"Classify these tables for erasure: {unknown}"


def test_erasure_lists_are_disjoint():
    """Verify that all erasure table classification lists are mutually disjoint with no duplicates."""
    all_lists = [
        ("BIOMETRIC_TABLES", BIOMETRIC_TABLES),
        ("ACCOUNT_TABLES", ACCOUNT_TABLES),
        ("ANONYMIZE_TABLES", ANONYMIZE_TABLES),
        ("RETAINED_MINIMAL", RETAINED_MINIMAL),
        ("CORE_AUTH", CORE_AUTH),
    ]

    # Verify no duplicates within any individual list
    for name, tbl_list in all_lists:
        assert len(tbl_list) == len(set(tbl_list)), (
            f"Duplicates found in {name}: {[t for t in tbl_list if tbl_list.count(t) > 1]}"
        )

    # Verify pairwise disjointness
    for i in range(len(all_lists)):
        name1, list1 = all_lists[i]
        set1 = set(list1)
        for j in range(i + 1, len(all_lists)):
            name2, list2 = all_lists[j]
            overlap = set1 & set(list2)
            assert not overlap, f"Tables overlap between {name1} and {name2}: {overlap}"


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
        - set(CORE_AUTH)
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
        cnt = db.execute(
            text(f'select count(*) from "{t}" where user_id = :u'), {"u": user_id}
        ).scalar()
        assert cnt == 0


@pytest.mark.db
def test_garments_sizes_in_stock_gin_index_exists(db_engine):
    """Assert that canonical_garments has the GIN index on sizes_in_stock in PostgreSQL."""
    with db_engine.connect() as conn:
        res = conn.execute(
            text(
                "SELECT indexname, indexdef FROM pg_indexes "
                "WHERE tablename = 'canonical_garments' AND indexdef LIKE '%gin%'"
            )
        ).fetchall()
        assert any("sizes_in_stock" in r[1] for r in res), "Expected GIN index on sizes_in_stock"


@pytest.mark.db
def test_erase_account_leaves_zero_residue_on_postgres(db, tmp_path):
    """End-to-end erasure test on real Postgres: seed user data, erase, assert zero rows, tombstone, outbox, and idempotency."""
    import asyncio

    user_id = uuid4()
    storage = LocalStorage(tmp_path)
    p_key = f"u/{user_id}/photos/portrait.jpg"
    storage.put(p_key, b"portrait_data", "image/jpeg")

    # Seed user and user-keyed rows
    db.execute(
        text('INSERT INTO "users" (id, created_at, updated_at) VALUES (:u, now(), now())'),
        {"u": user_id},
    )
    db.execute(
        text(
            'INSERT INTO "consent_records" (user_id, data_type, granted, consent_version, is_18_or_older, updated_at) VALUES (:u, :dt, true, :cv, true, now())'
        ),
        {"u": user_id, "dt": "terms_and_privacy", "cv": "2026.1"},
    )
    db.execute(
        text(
            'INSERT INTO "user_preferences" (user_id, categories, colors_favored, colors_avoided, updated_at) VALUES (:u, :cats, :fav, :av, now())'
        ),
        {"u": user_id, "cats": "[]", "fav": "[]", "av": "[]"},
    )
    db.flush()

    class OutboxCollector:
        def __init__(self):
            self.messages = []

        async def add(self, msg):
            self.messages.append(msg)

    class DirectUoW:
        def __init__(self, session):
            self.session = session
            self.outbox = OutboxCollector()

    uow = DirectUoW(db)
    # First erasure run
    asyncio.run(erase_account(uow, user_id, storage=storage))
    db.flush()

    assert storage.list_prefix(f"u/{user_id}/") == []
    for t in BIOMETRIC_TABLES:
        cnt = db.execute(
            text(f'select count(*) from "{t}" where user_id = :u'), {"u": user_id}
        ).scalar()
        assert cnt == 0, f"Expected 0 rows in biometric table {t}"
    for t in ACCOUNT_TABLES:
        if t == "users":
            continue
        cnt = db.execute(
            text(f'select count(*) from "{t}" where user_id = :u'), {"u": user_id}
        ).scalar()
        assert cnt == 0, f"Expected 0 rows in account table {t}"
    # Canonical user row deleted
    user_cnt = db.execute(
        text('select count(*) from "users" where id = :u'), {"u": user_id}
    ).scalar()
    assert user_cnt == 0, "Expected user row to be deleted"

    # Minimal pseudonymous tombstone recorded in erasure_tombstones
    tomb_cnt = db.execute(
        text('select count(*) from "erasure_tombstones" where user_id = :u'), {"u": user_id}
    ).scalar()
    assert tomb_cnt == 1, "Expected exactly 1 erasure tombstone recorded"

    # Outbox storage purge task enqueued
    assert len(uow.outbox.messages) >= 1
    assert any(getattr(m.event, "prefix", "") == f"u/{user_id}/" for m in uow.outbox.messages)

    # Second erasure run must be safe and idempotent
    res2 = asyncio.run(erase_account(uow, user_id, storage=storage))
    db.flush()
    assert res2["status"] == "account_erased"
    tomb_cnt2 = db.execute(
        text('select count(*) from "erasure_tombstones" where user_id = :u'), {"u": user_id}
    ).scalar()
    assert tomb_cnt2 == 1, "Tombstone must still be present after idempotent second run"


@pytest.mark.db
def test_erasure_classification_matches_database(db_engine):
    from fashx.application.erasure import (
        ACCOUNT_TABLES,
        ANONYMIZE_TABLES,
        BIOMETRIC_TABLES,
        CORE_AUTH,
        RETAINED_MINIMAL,
    )

    listed = (
        set(BIOMETRIC_TABLES)
        | set(ACCOUNT_TABLES)
        | set(ANONYMIZE_TABLES)
        | set(RETAINED_MINIMAL)
        | set(CORE_AUTH)
    )
    with db_engine.connect() as c:
        all_tables = {
            r[0]
            for r in c.execute(text("select tablename from pg_tables where schemaname='public'"))
        }
        by_column = {
            r[0]
            for r in c.execute(
                text(
                    "select table_name from information_schema.columns where table_schema='public' and column_name='user_id'"
                )
            )
        }
        by_fk = {
            r[0]
            for r in c.execute(
                text(
                    "select distinct tc.table_name from information_schema.table_constraints tc "
                    "join information_schema.constraint_column_usage ccu on ccu.constraint_name = tc.constraint_name "
                    "where tc.constraint_type='FOREIGN KEY' and tc.table_schema='public' and ccu.table_name in ('users','auth_identities')"
                )
            )
        }
    assert (by_column | by_fk) - listed == set(), "classify these user-linked tables for erasure"
    assert listed - all_tables == set(), "classified tables that do not exist (typo or renamed?)"


@pytest.mark.db
def test_loop_tables_all_have_user_id_column(db_engine):
    """Verify that every table deleted or anonymized by user_id in loops actually has a user_id column."""
    from fashx.application.erasure import (
        ACCOUNT_TABLES,
        ANONYMIZE_TABLES,
        BIOMETRIC_TABLES,
    )

    loop_tables = BIOMETRIC_TABLES + ACCOUNT_TABLES + ANONYMIZE_TABLES
    with db_engine.connect() as conn:
        existing_cols = conn.execute(
            text(
                "SELECT table_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND column_name = 'user_id'"
            )
        ).scalars().all()
    user_id_tables = set(existing_cols)
    for tbl in loop_tables:
        assert tbl in user_id_tables, f"Table '{tbl}' in erasure loop is missing a 'user_id' column"


@pytest.mark.db
def test_children_of_erased_tables_cascade(db_engine):
    """Verify that foreign keys pointing to erased tables either CASCADE, SET NULL, or have parent-child erasure ordering."""
    from fashx.application.erasure import (
        ACCOUNT_TABLES,
        BIOMETRIC_TABLES,
        CORE_AUTH,
    )

    erased_tables = set(BIOMETRIC_TABLES) | set(ACCOUNT_TABLES) | set(CORE_AUTH)
    with db_engine.connect() as conn:
        fks = conn.execute(
            text("""
                SELECT
                    tc.table_name AS child_table,
                    kcu.column_name AS child_column,
                    ccu.table_name AS parent_table,
                    rc.delete_rule AS delete_rule
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.referential_constraints rc
                    ON tc.constraint_name = rc.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON rc.unique_constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
            """)
        ).fetchall()

    for child_tbl, child_col, parent_tbl, rule in fks:
        if parent_tbl not in erased_tables:
            continue
        # If the parent is in erased tables, rule must be CASCADE or SET NULL,
        # UNLESS the child table is in BIOMETRIC_TABLES and explicitly deleted BEFORE the parent table!
        if rule not in ("CASCADE", "SET NULL"):
            if child_tbl in BIOMETRIC_TABLES and parent_tbl in BIOMETRIC_TABLES:
                child_idx = BIOMETRIC_TABLES.index(child_tbl)
                parent_idx = BIOMETRIC_TABLES.index(parent_tbl)
                assert child_idx < parent_idx, (
                    f"Child table '{child_tbl}' references '{parent_tbl}' with {rule}, "
                    f"so it must be deleted BEFORE '{parent_tbl}' (found child at {child_idx}, parent at {parent_idx})"
                )
            else:
                pytest.fail(
                    f"Foreign key {child_tbl}.{child_col} -> {parent_tbl} has non-cascading rule '{rule}' "
                    f"and is not ordered in erasure sequence"
                )


@pytest.mark.db
def test_erase_account_rolls_back_on_postgres_failure(db, tmp_path, monkeypatch):
    """When a statement fails during Postgres erasure, the entire transaction rolls back and no rows are erased."""
    import asyncio

    from fashx.application.erasure import ErasureIncomplete

    user_id = uuid4()
    storage = LocalStorage(tmp_path)

    # Seed user and user_photos row
    db.execute(
        text('INSERT INTO "users" (id, created_at, updated_at) VALUES (:u, now(), now())'),
        {"u": user_id},
    )
    db.execute(
        text(
            'INSERT INTO "user_photos" (id, user_id, photo_type, storage_key, status, version, created_at) '
            "VALUES (:id, :u, :pt, :sk, :st, 1, now())"
        ),
        {
            "id": uuid4(),
            "u": user_id,
            "pt": "body",
            "sk": f"u/{user_id}/photos/1.jpg",
            "st": "accepted",
        },
    )
    db.flush()

    class DirectUoW:
        def __init__(self, session):
            self.session = session
            self.outbox = None

    uow = DirectUoW(db)

    orig_exec = db.execute

    def failing_execute(statement, *args, **kwargs):
        if 'DELETE FROM "user_preferences"' in str(statement):
            raise RuntimeError("Injected database failure during account erasure")
        return orig_exec(statement, *args, **kwargs)

    monkeypatch.setattr(db, "execute", failing_execute)

    with pytest.raises(ErasureIncomplete):
        asyncio.run(erase_account(uow, user_id, storage=storage))

    # Rollback must restore all rows; user_photos must still exist
    cnt = db.execute(
        text('select count(*) from "user_photos" where user_id = :u'), {"u": user_id}
    ).scalar()
    assert cnt > 0, "Expected user_photos to still exist after transaction rollback"


@pytest.mark.xfail(reason="Supabase provider deletion pending auth project setup", strict=True)
def test_delete_me_deletes_supabase_auth_user():
    """Account deletion must invoke provider-side user deletion once Supabase auth project exists."""
    raise NotImplementedError("Supabase admin auth user deletion not yet wired")
