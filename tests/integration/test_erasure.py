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
    """End-to-end erasure test on real Postgres: seed user data across all classified tables, erase, assert zero rows, tombstone, outbox, and idempotency."""
    import asyncio
    import json

    user_id = uuid4()
    photo_id = uuid4()
    skin_id = uuid4()
    job_id = uuid4()
    garment_id = uuid4()
    merchant_id = uuid4()
    brand_id = uuid4()
    offer_id = uuid4()
    tenant_id = uuid4()
    click_id = uuid4()
    event_id = uuid4()
    invite_hash = f"hash-{uuid4()}"

    storage = LocalStorage(tmp_path)
    p_key = f"u/{user_id}/photos/portrait.jpg"
    storage.put(p_key, b"portrait_data", "image/jpeg")

    # Prerequisites (merchants, brands, garments, offers, tenants)
    db.execute(
        text('INSERT INTO "merchants" (id, name, merchant_type) VALUES (:m, :name, :mt)'),
        {"m": merchant_id, "name": "Test Merchant", "mt": "affiliate"},
    )
    db.execute(
        text('INSERT INTO "brands" (id, name, normalized_name) VALUES (:b, :name, :norm)'),
        {"b": brand_id, "name": "Test Brand", "norm": f"test-brand-{brand_id}"},
    )
    db.execute(
        text(
            'INSERT INTO "canonical_garments" (id, brand_id, display_name, category, tryon_supported, created_at, updated_at) '
            "VALUES (:g, :b, 'Garment', 'tops', false, now(), now())"
        ),
        {"g": garment_id, "b": brand_id},
    )
    db.execute(
        text(
            'INSERT INTO "merchant_offers" (id, garment_id, merchant_id, source_product_id, price_minor, currency, in_stock, url, last_synced_at) '
            "VALUES (:o, :g, :m, :spid, 1000, 'INR', true, 'https://example.com', now())"
        ),
        {"o": offer_id, "g": garment_id, "m": merchant_id, "spid": f"src-{offer_id}"},
    )
    db.execute(
        text('INSERT INTO "tenants" (id, slug, name, created_at, updated_at) VALUES (:t, :slug, :name, now(), now())'),
        {"t": tenant_id, "slug": f"slug-{tenant_id}", "name": "Test Tenant"},
    )

    # Core user & auth identities
    db.execute(
        text('INSERT INTO "users" (id, created_at, updated_at) VALUES (:u, now(), now())'),
        {"u": user_id},
    )
    db.execute(
        text('INSERT INTO "auth_identities" (id, issuer, subject, user_id, created_at) VALUES (:aid, :iss, :sub, :u, now())'),
        {"aid": uuid4(), "iss": "local", "sub": f"sub-{uuid4()}", "u": user_id},
    )

    # Biometric tables
    db.execute(
        text(
            'INSERT INTO "user_photos" (id, user_id, photo_type, storage_key, status, version, created_at) '
            "VALUES (:pid, :u, 'body', :sk, 'accepted', 1, now())"
        ),
        {"pid": photo_id, "u": user_id, "sk": f"u/{user_id}/photos/1.jpg"},
    )
    db.execute(
        text(
            'INSERT INTO "skin_tone_results" (id, user_id, photo_id, confidence, method, model_version, status, created_at) '
            "VALUES (:sid, :u, :pid, 0.95, 'colorimetry', '1.0', 'accepted', now())"
        ),
        {"sid": skin_id, "u": user_id, "pid": photo_id},
    )
    db.execute(
        text(
            'INSERT INTO "profile_artifacts" (id, user_id, version, body_snapshot, preferences_snapshot, tryon_photo_id, skin_tone_result_id, created_at) '
            "VALUES (:paid, :u, 1, :bs, :ps, :pid, :sid, now())"
        ),
        {"paid": uuid4(), "u": user_id, "bs": json.dumps({}), "ps": json.dumps({}), "pid": photo_id, "sid": skin_id},
    )
    db.execute(
        text('INSERT INTO "profile_photo_jobs" (id, user_id, photo_id, status, created_at) VALUES (:ppjid, :u, :pid, :st, now())'),
        {"ppjid": uuid4(), "u": user_id, "pid": photo_id, "st": "completed"},
    )
    db.execute(
        text(
            'INSERT INTO "tryon_jobs" (id, user_id, garment_id, profile_photo_id, idempotency_key, artifact_key, model_version, pipeline_version, created_at) '
            "VALUES (:jid, :u, :g, :pid, :idem, 'art.jpg', '1.0', '1.0', now())"
        ),
        {"jid": job_id, "u": user_id, "g": garment_id, "pid": photo_id, "idem": str(uuid4())},
    )
    db.execute(
        text(
            'INSERT INTO "media_objects" (id, user_id, kind, object_key, sha256, size_bytes, content_type, created_at) '
            "VALUES (:mid, :u, 'reference_photo', :sk, :sha, 1024, 'image/jpeg', now())"
        ),
        {"mid": uuid4(), "u": user_id, "sk": f"u/{user_id}/media/1.jpg", "sha": "a" * 64},
    )
    db.execute(
        text('INSERT INTO "body_profiles" (user_id, height_cm, weight_kg, version) VALUES (:u, 175, 70, 1)'),
        {"u": user_id},
    )
    db.execute(
        text(
            'INSERT INTO "user_measurements" (id, user_id, measurement, value, unit, source) '
            "VALUES (:umid, :u, 'chest', 95.0, 'cm', 'user')"
        ),
        {"umid": uuid4(), "u": user_id},
    )
    db.execute(
        text('INSERT INTO "user_style_profiles" (user_id, embedding, model_version, version) VALUES (:u, :emb, :mv, 1)'),
        {"u": user_id, "emb": "[" + ",".join(["0.1"] * 512) + "]", "mv": "1.0"},
    )

    # Account tables
    db.execute(
        text(
            'INSERT INTO "wardrobe_items" (id, user_id, garment_id, offer_id, snapshot_title, snapshot_price_minor, snapshot_image_key) '
            "VALUES (:wid, :u, :g, :o, 'Shirt', 1999, 'shirt.jpg')"
        ),
        {"wid": uuid4(), "u": user_id, "g": garment_id, "o": offer_id},
    )
    db.execute(
        text('INSERT INTO "buy_clicks" (id, user_id, garment_id, offer_id, clicked_at) VALUES (:cid, :u, :g, :o, now())'),
        {"cid": click_id, "u": user_id, "g": garment_id, "o": offer_id},
    )
    db.execute(
        text(
            'INSERT INTO "fit_feedback" (id, user_id, garment_id, brand_id, buy_click_id, category, size_label, verdict, created_at) '
            "VALUES (:ffid, :u, :g, :b, :cid, 'tops', 'M', 'fit', now())"
        ),
        {"ffid": uuid4(), "u": user_id, "g": garment_id, "b": brand_id, "cid": click_id},
    )
    db.execute(
        text('INSERT INTO "tryon_feedback" (id, user_id, tryon_job_id, visual_accuracy, created_at) VALUES (:tfid, :u, :jid, :va, now())'),
        {"tfid": uuid4(), "u": user_id, "jid": job_id, "va": "accurate"},
    )
    db.execute(
        text('INSERT INTO "feed_exclusions" (user_id, garment_id, created_at) VALUES (:u, :g, now())'),
        {"u": user_id, "g": garment_id},
    )
    db.execute(
        text(
            'INSERT INTO "feed_impressions" (id, user_id, session_id, garment_id, position, ranker_version, created_at) '
            "VALUES (:fiid, :u, :sess, :g, 1, '1.0', now())"
        ),
        {"fiid": uuid4(), "u": user_id, "sess": uuid4(), "g": garment_id},
    )
    db.execute(
        text('INSERT INTO "feed_signals" (user_id, garment_id, action, created_at) VALUES (:u, :g, :act, now())'),
        {"u": user_id, "g": garment_id, "act": "like"},
    )
    db.execute(
        text('INSERT INTO "user_preferences" (user_id, colors_favored, colors_avoided, categories, updated_at) VALUES (:u, :cf, :ca, :cats, now())'),
        {"u": user_id, "cf": json.dumps([]), "ca": json.dumps([]), "cats": json.dumps([])},
    )
    db.execute(
        text('INSERT INTO "onboarding_profiles" (user_id, status, step, created_at, updated_at) VALUES (:u, :st, :step, now(), now())'),
        {"u": user_id, "st": "completed", "step": "done"},
    )
    db.execute(
        text(
            'INSERT INTO "consent_records" (user_id, data_type, granted, consent_version, is_18_or_older, updated_at) '
            "VALUES (:u, :dt, true, :cv, true, now())"
        ),
        {"u": user_id, "dt": "terms_and_privacy", "cv": "2026.1"},
    )
    db.execute(
        text('INSERT INTO "style_quiz_picks" (id, user_id, garment_id, liked, created_at) VALUES (:sqpid, :u, :g, true, now())'),
        {"sqpid": uuid4(), "u": user_id, "g": garment_id},
    )
    db.execute(
        text(
            'INSERT INTO "idempotency_records" (id, user_id, key, request_hash, state, created_at, expires_at) '
            "VALUES (:irid, :u, :k, :rh, 'completed', now(), now())"
        ),
        {"irid": uuid4(), "u": user_id, "k": f"key-{uuid4()}", "rh": "h" * 64},
    )
    db.execute(
        text('INSERT INTO "pilot_participants" (user_id, cohort, channel, joined_at) VALUES (:u, :coh, :ch, now())'),
        {"u": user_id, "coh": "alpha", "ch": "mobile"},
    )
    db.execute(
        text('INSERT INTO "pilot_survey_responses" (id, user_id, survey_key, answers, created_at) VALUES (:psrid, :u, :sk, :ans, now())'),
        {"psrid": uuid4(), "u": user_id, "sk": "alpha_survey", "ans": json.dumps({"q": 1})},
    )
    db.execute(
        text('INSERT INTO "pilot_feedback" (id, user_id, kind, message, created_at) VALUES (:pfid, :u, :k, :msg, now())'),
        {"pfid": uuid4(), "u": user_id, "k": "bug", "msg": "feedback"},
    )
    db.execute(
        text('INSERT INTO "experiment_exposures" (id, user_id, experiment, variant, first_seen_at) VALUES (:eeid, :u, :exp, :var, now())'),
        {"eeid": uuid4(), "u": user_id, "exp": "feed_v2", "var": "test"},
    )
    db.execute(
        text('INSERT INTO "tenant_members" (id, tenant_id, user_id, role, created_at) VALUES (:tmid, :t, :u, :r, now())'),
        {"tmid": uuid4(), "t": tenant_id, "u": user_id, "r": "member"},
    )

    # Anonymize tables (user_id will become NULL)
    db.execute(
        text('INSERT INTO "domain_events" (id, event_type, user_id, occurred_at) VALUES (:deid, :et, :u, now())'),
        {"deid": event_id, "et": "user.signed_up", "u": user_id},
    )
    db.execute(
        text('INSERT INTO "pilot_invites" (code_hash, cohort, channel, user_id, created_at) VALUES (:ch, :coh, :channel, :u, now())'),
        {"ch": invite_hash, "coh": "alpha", "channel": "mobile", "u": user_id},
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

    # Storage prefix is wiped
    assert storage.list_prefix(f"u/{user_id}/") == []

    # All biometric tables are empty for user
    for t in BIOMETRIC_TABLES:
        cnt = db.execute(
            text(f'select count(*) from "{t}" where user_id = :u'), {"u": user_id}
        ).scalar()
        assert cnt == 0, f"Expected 0 rows in biometric table {t}"

    # All account tables are empty for user
    for t in ACCOUNT_TABLES:
        cnt = db.execute(
            text(f'select count(*) from "{t}" where user_id = :u'), {"u": user_id}
        ).scalar()
        assert cnt == 0, f"Expected 0 rows in account table {t}"

    # Core auth: identities and canonical user row deleted
    auth_cnt = db.execute(
        text('select count(*) from "auth_identities" where user_id = :u'), {"u": user_id}
    ).scalar()
    assert auth_cnt == 0, "Expected auth_identities rows to be deleted"

    user_cnt = db.execute(
        text('select count(*) from "users" where id = :u'), {"u": user_id}
    ).scalar()
    assert user_cnt == 0, "Expected user row to be deleted"

    # Anonymized tables: rows retained but user_id disassociated to NULL
    de_user_cnt = db.execute(
        text('select count(*) from "domain_events" where user_id = :u'), {"u": user_id}
    ).scalar()
    assert de_user_cnt == 0, "Expected 0 domain_events with user_id"
    de_null_cnt = db.execute(
        text('select count(*) from "domain_events" where id = :deid and user_id IS NULL'), {"deid": event_id}
    ).scalar()
    assert de_null_cnt == 1, "Expected domain_event to be anonymized with user_id = NULL"

    pi_user_cnt = db.execute(
        text('select count(*) from "pilot_invites" where user_id = :u'), {"u": user_id}
    ).scalar()
    assert pi_user_cnt == 0, "Expected 0 pilot_invites with user_id"
    pi_null_cnt = db.execute(
        text('select count(*) from "pilot_invites" where code_hash = :ch and user_id IS NULL'), {"ch": invite_hash}
    ).scalar()
    assert pi_null_cnt == 1, "Expected pilot_invite to be anonymized with user_id = NULL"

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
    """Verify that foreign keys pointing to erased tables either CASCADE or SET NULL."""
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
        assert rule in (
            "CASCADE",
            "SET NULL",
        ), f"Foreign key {child_tbl}.{child_col} -> {parent_tbl} has non-cascading rule '{rule}'"


@pytest.mark.db
def test_erase_account_rolls_back_on_postgres_failure(db, tmp_path, monkeypatch):
    """When a statement fails during Postgres erasure, the entire transaction rolls back and no rows are erased (nothing half-deleted)."""
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

    # Rollback must restore all rows; user and user_photos must still exist, and zero tombstones recorded
    user_cnt = db.execute(
        text('select count(*) from "users" where id = :u'), {"u": user_id}
    ).scalar()
    assert user_cnt == 1, "Expected user to still exist after transaction rollback"

    photo_cnt = db.execute(
        text('select count(*) from "user_photos" where user_id = :u'), {"u": user_id}
    ).scalar()
    assert photo_cnt == 1, "Expected user_photos to still exist after transaction rollback"

    tomb_cnt = db.execute(
        text('select count(*) from "erasure_tombstones" where user_id = :u'), {"u": user_id}
    ).scalar()
    assert tomb_cnt == 0, "Expected zero tombstones written when erasure failed and rolled back"


@pytest.mark.xfail(reason="Supabase provider deletion pending auth project setup", strict=True)
def test_delete_me_deletes_supabase_auth_user():
    """Account deletion must invoke provider-side user deletion once Supabase auth project exists."""
    raise NotImplementedError("Supabase admin auth user deletion not yet wired")
