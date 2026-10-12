import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy import func, select, update

from database.models.pilot import (
    PilotFeedback,
    PilotInvite,
    PilotParticipant,
    PilotSurveyResponse,
)
from database.models.tryon import TryOnJob
from fashx.core.database import get_db_session
from fashx.core.flags import END_SURVEY_OPEN, is_flag_enabled
from fashx.pilot.schemas import (
    EndOfPilot,
    FeedDay5,
    JoinPilotRequest,
    JoinPilotResponse,
    PendingSurveyResponse,
    PilotFeedbackRequest,
    SubmitSurveyRequest,
    TryonFirst,
)
from fashx.security.deps import Principal, get_principal

logger = logging.getLogger("fashx.pilot.router")
router = APIRouter(prefix="/pilot", tags=["pilot"])


def hash_invite_code(code: str) -> str:
    """Normalize and hash invite code for lookup."""
    return hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()


@router.post("/join", response_model=JoinPilotResponse)
async def join_pilot(
    payload: JoinPilotRequest,
    principal: Principal = Depends(get_principal),
) -> JoinPilotResponse:
    """Redeem a single-use invite code to join a pilot cohort (Rule 10.4)."""
    user_id = UUID(principal.user_id)
    code_h = hash_invite_code(payload.code)

    async for session in get_db_session():
        # Concurrently safe with FOR UPDATE lock
        stmt = (
            select(PilotInvite)
            .where(PilotInvite.code_hash == code_h)
            .with_for_update()
        )
        res = await session.execute(stmt)
        invite = res.scalar_one_or_none()

        # Identical 404 for invalid code and already-used code to avoid enumeration
        if invite is None or invite.used_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired invite code",
            )

        now = datetime.now(UTC)
        invite.used_at = now
        invite.user_id = user_id

        # Record or update pilot participant
        participant = PilotParticipant(
            user_id=user_id,
            cohort=invite.cohort,
            channel=invite.channel,
            joined_at=now,
            os=payload.os,
            app_version=payload.app_version,
        )
        session.add(participant)
        await session.commit()

        return JoinPilotResponse(
            cohort=invite.cohort,
            channel=invite.channel,
            joined_at=now,
        )

    raise HTTPException(status_code=500, detail="Database session unavailable")


@router.post("/feedback")
async def submit_feedback(
    payload: PilotFeedbackRequest,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    """Submit qualitative feedback during the pilot (Rule 10.4)."""
    user_id = UUID(principal.user_id)

    async for session in get_db_session():
        entry = PilotFeedback(
            user_id=user_id,
            kind=payload.kind,
            message=payload.message,
            context=payload.context,
        )
        session.add(entry)
        await session.commit()
        return {"status": "recorded"}

    raise HTTPException(status_code=500, detail="Database session unavailable")


@router.get("/surveys/pending", response_model=PendingSurveyResponse)
async def get_pending_survey(
    principal: Principal = Depends(get_principal),
) -> PendingSurveyResponse:
    """Determine the next appropriate pending survey for the participant (Rule 10.4)."""
    user_id = UUID(principal.user_id)

    async for session in get_db_session():
        # 1. Fetch answered survey keys
        answered_stmt = select(PilotSurveyResponse.survey_key).where(
            PilotSurveyResponse.user_id == user_id
        )
        res_answered = await session.execute(answered_stmt)
        answered = set(res_answered.scalars().all())

        # 2. Check tryon_first: completed at least 1 tryon job
        if "tryon_first" not in answered:
            tryon_stmt = (
                select(TryOnJob.id)
                .where(TryOnJob.user_id == user_id, TryOnJob.status == "completed")
                .limit(1)
            )
            has_tryon = (await session.execute(tryon_stmt)).scalar_one_or_none()
            if has_tryon is not None:
                return PendingSurveyResponse(
                    survey_key="tryon_first",
                    description="First Virtual Try-On Experience Feedback",
                )

        # 3. Check feed_day5: joined >= 5 days ago
        if "feed_day5" not in answered:
            part_stmt = select(PilotParticipant).where(PilotParticipant.user_id == user_id)
            participant = (await session.execute(part_stmt)).scalar_one_or_none()
            if participant and participant.joined_at <= datetime.now(UTC) - timedelta(days=5):
                return PendingSurveyResponse(
                    survey_key="feed_day5",
                    description="Discovery Feed 5-Day Check-In",
                )

        # 4. Check end_of_pilot: feature flag active
        if "end_of_pilot" not in answered:
            is_open = await is_flag_enabled(END_SURVEY_OPEN, default=False, session=session)
            if is_open:
                return PendingSurveyResponse(
                    survey_key="end_of_pilot",
                    description="Final Pilot Evaluation & System Usability Scale (SUS)",
                )

        return PendingSurveyResponse(survey_key=None, description=None)

    raise HTTPException(status_code=500, detail="Database session unavailable")


@router.post("/survey")
async def submit_survey(
    payload: SubmitSurveyRequest,
    principal: Principal = Depends(get_principal),
) -> dict[str, str]:
    """Validate and record a completed survey submission (Rule 10.4)."""
    user_id = UUID(principal.user_id)

    # Validate against strict Pydantic model with extra="forbid"
    try:
        if payload.survey_key == "tryon_first":
            validated = TryonFirst(**payload.answers).model_dump()
        elif payload.survey_key == "feed_day5":
            validated = FeedDay5(**payload.answers).model_dump()
        elif payload.survey_key == "end_of_pilot":
            validated = EndOfPilot(**payload.answers).model_dump()
        else:
            raise HTTPException(status_code=400, detail="Unknown survey key")
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid survey answers format: {e.errors()}",
        ) from e

    async for session in get_db_session():
        # Check if already submitted (enforces uq_survey_once)
        check_stmt = select(PilotSurveyResponse.id).where(
            PilotSurveyResponse.user_id == user_id,
            PilotSurveyResponse.survey_key == payload.survey_key,
        )
        existing = (await session.execute(check_stmt)).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Survey '{payload.survey_key}' has already been submitted",
            )

        resp = PilotSurveyResponse(
            user_id=user_id,
            survey_key=payload.survey_key,
            answers=validated,
        )
        session.add(resp)
        await session.commit()
        return {"status": "recorded", "survey_key": payload.survey_key}

    raise HTTPException(status_code=500, detail="Database session unavailable")
