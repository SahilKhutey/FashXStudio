from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from fashx.application.retention import (
    anonymize_analytics,
    cleanup_impressions,
    cleanup_unsaved_tryons,
    run_daily_retention,
)


@pytest.mark.asyncio
async def test_cleanup_unsaved_tryons_purges_storage_and_records():
    # Setup mock session and storage
    mock_session = AsyncMock()
    mock_storage = MagicMock()

    artifact_id = uuid4()
    job_id = uuid4()
    fake_rows = [
        (artifact_id, job_id, "tryon/result_01.jpg", "tryon/artifact_01.json")
    ]

    # First execute call returns unreferenced candidate rows
    first_res = MagicMock()
    first_res.fetchall.return_value = fake_rows

    # Second execute call deletes job ids
    second_res = MagicMock()
    second_res.rowcount = 1

    # Third execute call deletes orphan jobs
    third_res = MagicMock()
    third_res.rowcount = 0

    mock_session.execute.side_effect = [first_res, second_res, third_res]

    res = await cleanup_unsaved_tryons(
        session=mock_session,
        storage=mock_storage,
        cutoff_days=30,
        batch_size=500,
    )

    assert res["tryon_jobs_deleted"] == 1
    assert res["storage_keys_purged"] == 2
    mock_storage.delete.assert_any_call("tryon/result_01.jpg")
    mock_storage.delete.assert_any_call("tryon/artifact_01.json")


@pytest.mark.asyncio
async def test_cleanup_impressions_deletes_older_than_cutoff():
    mock_session = AsyncMock()
    del_res = MagicMock()
    del_res.rowcount = 42
    mock_session.execute.return_value = del_res

    deleted_count = await cleanup_impressions(session=mock_session, cutoff_days=90, batch_size=500)

    assert deleted_count == 42
    assert mock_session.execute.called


@pytest.mark.asyncio
async def test_anonymize_analytics_strips_user_id():
    mock_session = AsyncMock()
    update_res = MagicMock()
    update_res.rowcount = 120
    mock_session.execute.return_value = update_res

    anonymized_count = await anonymize_analytics(session=mock_session, cutoff_days=365, batch_size=500)

    assert anonymized_count == 120
    assert mock_session.execute.called


@pytest.mark.asyncio
async def test_run_daily_retention_orchestration():
    mock_session = AsyncMock()
    mock_storage = MagicMock()

    # Configure session executes for all 3 sub-jobs
    # 1. tryons: fetchall empty, orphan 0
    res_tryon_fetch = MagicMock()
    res_tryon_fetch.fetchall.return_value = []
    res_tryon_orphan = MagicMock()
    res_tryon_orphan.rowcount = 0

    # 2. impressions: rowcount 15
    res_impr = MagicMock()
    res_impr.rowcount = 15

    # 3. analytics: rowcount 5
    res_ana = MagicMock()
    res_ana.rowcount = 5

    mock_session.execute.side_effect = [
        res_tryon_fetch,
        res_tryon_orphan,
        res_impr,
        res_ana,
    ]

    summary = await run_daily_retention(session=mock_session, storage=mock_storage)

    assert summary["status"] == "success"
    assert summary["tryon_jobs_deleted"] == 0
    assert summary["impressions_deleted"] == 15
    assert summary["analytics_events_anonymized"] == 5
