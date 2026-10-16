from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from fashx.application.erasure import erase_account
from fashx.pilot.router import hash_invite_code
from fashx.pilot.schemas import (
    EndOfPilot,
    PilotFeedbackRequest,
    TryonFirst,
)


def test_invite_code_hashing_consistency():
    code_raw = "w1-alpha-99"
    h1 = hash_invite_code(code_raw)
    h2 = hash_invite_code(" W1-ALPHA-99 ")
    assert h1 == h2
    assert len(h1) == 64


def test_tryon_first_survey_validation():
    # Valid answers
    valid = TryonFirst(looked_like_me=4, trust_for_buying=5, comment="Looks great")
    assert valid.looked_like_me == 4
    assert valid.trust_for_buying == 5

    # Out of range Likert
    with pytest.raises(ValidationError):
        TryonFirst(looked_like_me=6, trust_for_buying=3)

    with pytest.raises(ValidationError):
        TryonFirst(looked_like_me=0, trust_for_buying=3)

    # Extra keys rejected by extra="forbid"
    with pytest.raises(ValidationError):
        TryonFirst(looked_like_me=4, trust_for_buying=4, unknown_field="injected")


def test_end_of_pilot_survey_validation():
    valid_sus = [4, 2, 5, 1, 4, 2, 5, 1, 4, 2]  # exactly 10 items
    valid = EndOfPilot(
        sus=valid_sus,
        disappointed="very",
        nps=9,
        photo_comfort=5,
        would_use_weekly=4,
        bought_any=True,
        bought_notes="Bought Snitch shirt",
        best="Virtual try-on accuracy",
        worst="Limited ethnic wear",
    )
    assert valid.nps == 9
    assert valid.disappointed == "very"

    # Too few SUS items (< 10)
    with pytest.raises(ValidationError):
        EndOfPilot(
            sus=[4, 2, 5],
            disappointed="very",
            nps=9,
            photo_comfort=5,
            would_use_weekly=4,
            bought_any=False,
        )

    # Out of bounds NPS (> 10)
    with pytest.raises(ValidationError):
        EndOfPilot(
            sus=valid_sus,
            disappointed="very",
            nps=11,
            photo_comfort=5,
            would_use_weekly=4,
            bought_any=False,
        )


def test_pilot_feedback_context_sanitization():
    req = PilotFeedbackRequest(
        kind="bug",
        message="Button misaligned on small screen",
        context={
            "screen": "TryOnModal",
            "app_version": "1.0.0-pilot",
            "job_id": "job-123",
            "leaked_user_email": "attacker@evil.com",  # Should be dropped by validator
        },
    )
    assert "screen" in req.context
    assert "app_version" in req.context
    assert "job_id" in req.context
    assert "leaked_user_email" not in req.context


@pytest.mark.asyncio
async def test_erase_account_cascades_pilot_tables():
    user_id = uuid4()
    mock_uow = MagicMock(spec=["session", "commit", "rollback"])
    mock_session = AsyncMock()
    mock_session.expunge_all = MagicMock()
    mock_uow.session = mock_session
    mock_uow.commit = AsyncMock()
    mock_uow.rollback = AsyncMock()

    res = await erase_account(mock_uow, user_id=user_id)
    assert res["status"] == "account_erased"

    executed_sqls = [call.args[0].text for call in mock_session.execute.call_args_list]

    # Verify pilot_participants, pilot_survey_responses, pilot_feedback are deleted
    assert any('DELETE FROM "pilot_participants"' in sql for sql in executed_sqls)
    assert any('DELETE FROM "pilot_survey_responses"' in sql for sql in executed_sqls)
    assert any('DELETE FROM "pilot_feedback"' in sql for sql in executed_sqls)

    # Verify pilot_invites user_id is set to NULL (anonymized)
    assert any('UPDATE "pilot_invites" SET user_id = NULL' in sql for sql in executed_sqls)
