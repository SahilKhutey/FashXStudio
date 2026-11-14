"""Tests for dead-letter payload sanitization and database persistence."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from database.models.operations import WorkerDeadLetter
from fashx.workers.dead_letter import (
    _persist_dead_letter_async,
    build_safe_payload,
    persist_dead_letter_sync,
)


def test_build_safe_payload_extracts_approved_identifiers() -> None:
    job_id = str(uuid4())
    payload = build_safe_payload(
        "fashx.workers.app.process_tryon_job",
        (job_id,),
        {},
    )
    assert payload == {"job_id": job_id}

    source_id = str(uuid4())
    payload = build_safe_payload(
        "fashx.workers.app.ingest_catalog_feed",
        (),
        {"source_id": source_id, "extra": "ignored"},
    )
    assert payload == {"source_id": source_id}

    garment_id = str(uuid4())
    payload = build_safe_payload(
        "fashx.workers.app.enrich_garment_task",
        (garment_id,),
        {"extra_token": "secret"},
    )
    assert payload == {"garment_id": garment_id}


def test_build_safe_payload_filters_sensitive_urls_and_tokens() -> None:
    # URL disguised as identifier
    payload_url = build_safe_payload(
        "fashx.workers.app.process_tryon_job",
        ("https://s3.ap-south-1.amazonaws.com/media/user_photo.jpg?X-Amz-Signature=secret",),
        {},
    )
    assert payload_url == {}

    # Bearer token disguised as identifier
    payload_token = build_safe_payload(
        "fashx.workers.app.process_tryon_job",
        ("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",),
        {},
    )
    assert payload_token == {}


def test_build_safe_payload_unknown_task_returns_empty() -> None:
    payload = build_safe_payload(
        "fashx.workers.app.unknown_task",
        ("arg1",),
        {"key": "value"},
    )
    assert payload == {}


@pytest.mark.asyncio
async def test_persist_dead_letter_async_inserts_new_record() -> None:
    task_id = str(uuid4())
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.add = MagicMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session
    mock_factory.return_value.__aexit__.return_value = None

    with patch("fashx.workers.dead_letter.get_session_factory", return_value=mock_factory):
        await _persist_dead_letter_async(
            task_id=task_id,
            task_name="fashx.workers.app.process_tryon_job",
            queue_name="tryon",
            error_type="TimeoutError",
            error_message="Provider timeout after 90 seconds" * 50,  # exceeds 1000 chars
            safe_payload={"job_id": "test-job-id"},
            attempts=3,
        )

        assert mock_session.add.called
        added_record = mock_session.add.call_args[0][0]
        assert isinstance(added_record, WorkerDeadLetter)
        assert added_record.task_id == task_id
        assert added_record.queue_name == "tryon"
        assert len(added_record.error_message) <= 1000
        assert added_record.safe_payload == {"job_id": "test-job-id"}
        assert added_record.attempts == 3
        assert mock_session.commit.called


@pytest.mark.asyncio
async def test_persist_dead_letter_async_updates_existing_record() -> None:
    task_id = str(uuid4())
    existing_record = WorkerDeadLetter(
        task_id=task_id,
        task_name="fashx.workers.app.process_tryon_job",
        queue_name="tryon",
        error_type="InitialError",
        error_message="Initial failure",
        safe_payload={"job_id": "initial"},
        attempts=1,
    )

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_record
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session
    mock_factory.return_value.__aexit__.return_value = None

    with patch("fashx.workers.dead_letter.get_session_factory", return_value=mock_factory):
        await _persist_dead_letter_async(
            task_id=task_id,
            task_name="fashx.workers.app.process_tryon_job",
            queue_name="tryon",
            error_type="UpdatedError",
            error_message="Updated failure message",
            safe_payload={"job_id": "updated"},
            attempts=2,
        )

        assert existing_record.error_type == "UpdatedError"
        assert existing_record.error_message == "Updated failure message"
        assert existing_record.attempts == 2
        assert existing_record.safe_payload == {"job_id": "updated"}
        assert mock_session.commit.called


def test_persist_dead_letter_sync_catches_and_logs_database_error(caplog: pytest.LogCaptureFixture) -> None:
    with patch("fashx.workers.dead_letter._persist_dead_letter_async", side_effect=RuntimeError("Database down")):
        with caplog.at_level(logging.ERROR):
            # Must not raise exception to the caller
            persist_dead_letter_sync(
                task_id="task-123",
                task_name="test_task",
                queue_name="test_queue",
                error_type="FatalError",
                error_message="Failed",
                safe_payload={},
            )
            assert "CRITICAL: Failed to persist dead letter" in caplog.text
