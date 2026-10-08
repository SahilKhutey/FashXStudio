from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fashx.commerce_wardrobe.application.submit_fit_feedback import (
    SubmitFitFeedbackCommand,
    SubmitFitFeedbackUseCase,
)
from fashx.commerce_wardrobe.application.submit_tryon_feedback import (
    SubmitTryOnFeedbackCommand,
    SubmitTryOnFeedbackUseCase,
)
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from api.app.core.errors import ValidationError


@pytest.mark.asyncio
async def test_fit_feedback_and_sizing_bias_learning(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CommerceWardrobeUnitOfWork(session_factory)
    uc = SubmitFitFeedbackUseCase(uow)

    user_a = uuid4()
    user_b = uuid4()
    user_c = uuid4()
    brand_id = uuid4()
    garment_id = uuid4()

    # 1. Invalid verdict raises ValidationError
    with pytest.raises(ValidationError):
        await uc.execute(
            SubmitFitFeedbackCommand(
                user_id=user_a,
                garment_id=garment_id,
                brand_id=brand_id,
                category="tops",
                size_label="M",
                verdict="way_too_small",  # Invalid
            )
        )

    # 2. Record: 3 users report "too_tight" for this brand
    res1 = await uc.execute(
        SubmitFitFeedbackCommand(
            user_id=user_a,
            garment_id=garment_id,
            brand_id=brand_id,
            category="tops",
            size_label="M",
            verdict="too_tight",
        )
    )
    assert res1.total_observations == 1
    assert res1.brand_bias_score == -1.0
    assert res1.brand_recommendation == "size_up"

    await uc.execute(
        SubmitFitFeedbackCommand(
            user_id=user_b,
            garment_id=garment_id,
            brand_id=brand_id,
            category="tops",
            size_label="L",
            verdict="too_tight",
        )
    )
    res3 = await uc.execute(
        SubmitFitFeedbackCommand(
            user_id=user_c,
            garment_id=garment_id,
            brand_id=brand_id,
            category="tops",
            size_label="S",
            verdict="too_tight",
        )
    )
    assert res3.total_observations == 3
    assert res3.brand_bias_score == -1.0
    assert res3.brand_recommendation == "size_up"

    # 3. Query Brand Calibration
    async with uow:
        metrics = await uow.fit_feedback.compute_brand_bias(brand_id, "tops")
        assert metrics["total_observations"] == 3
        assert metrics["recommendation"] == "size_up"
        assert metrics["too_tight_pct"] == 100.0


@pytest.mark.asyncio
async def test_tryon_feedback_collection(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    uow = CommerceWardrobeUnitOfWork(session_factory)
    uc = SubmitTryOnFeedbackUseCase(uow)

    user_id = uuid4()
    job_id = uuid4()

    # 1. Invalid accuracy raises ValidationError
    with pytest.raises(ValidationError):
        await uc.execute(
            SubmitTryOnFeedbackCommand(
                user_id=user_id,
                tryon_job_id=job_id,
                visual_accuracy="hyper_realistic",  # Invalid enum value
            )
        )

    # 2. Invalid confidence rating out of 1..5 range raises ValidationError
    with pytest.raises(ValidationError):
        await uc.execute(
            SubmitTryOnFeedbackCommand(
                user_id=user_id,
                tryon_job_id=job_id,
                visual_accuracy="accurate",
                purchase_confidence=10,  # Range is 1..5
            )
        )

    # 3. Successful recording
    res = await uc.execute(
        SubmitTryOnFeedbackCommand(
            user_id=user_id,
            tryon_job_id=job_id,
            visual_accuracy="accurate",
            purchase_confidence=4,
        )
    )
    assert res.feedback_id is not None
    assert res.visual_accuracy == "accurate"
    assert res.purchase_confidence == 4
