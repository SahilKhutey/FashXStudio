"""FastAPI v1 endpoints for Phase 08.5 Feedback Loop."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from fashx.api.v1.ranking import get_ranking_service
from fashx.feedback.consent import FeedbackConsentService
from fashx.feedback.contracts import (
    ConsentStateResponse,
    ConsentUpdateRequest,
    FeedbackEventRequest,
    FeedbackEventResponse,
    OutboundClickRequest,
    OutboundClickResponse,
    ReactionResponse,
    ReactionUpdateRequest,
    SavedProductResponse,
    SaveProductRequest,
    VTOQualityFeedbackRequest,
    VTOQualityFeedbackResponse,
)
from fashx.feedback.enums import ConsentPurpose, FeedbackEventType, ReactionState
from fashx.feedback.idempotency import FeedbackConflict
from fashx.feedback.ingestion import FeedbackIngestionService
from fashx.feedback.metrics import compute_feedback_monitoring
from fashx.feedback.processing import FeedbackProcessor
from fashx.feedback.repository import InMemoryFeedbackRepository
from fashx.ranking.service import PersonalizedRankingService
from fashx.security.deps import Principal, get_principal

router = APIRouter(tags=["feedback-loop"])

_SHARED_FEEDBACK_REPO = InMemoryFeedbackRepository()
_SHARED_CONSENT_SERVICE = FeedbackConsentService()


def get_feedback_repository() -> InMemoryFeedbackRepository:
    return _SHARED_FEEDBACK_REPO


def get_feedback_consent_service() -> FeedbackConsentService:
    return _SHARED_CONSENT_SERVICE


def _ensure_personalized_consent_or_default(
    consent_service: FeedbackConsentService, shopper_id: str
) -> None:
    if consent_service.get_latest(shopper_id, ConsentPurpose.PERSONALIZED_RANKING) is None:
        consent_service.set_consent(
            shopper_id=shopper_id,
            purpose=ConsentPurpose.PERSONALIZED_RANKING,
            granted=True,
            source="default",
        )
    if consent_service.get_latest(shopper_id, ConsentPurpose.FEEDBACK_EVALUATION) is None:
        consent_service.set_consent(
            shopper_id=shopper_id,
            purpose=ConsentPurpose.FEEDBACK_EVALUATION,
            granted=True,
            source="default",
        )
    if consent_service.get_latest(shopper_id, ConsentPurpose.PRODUCT_ANALYTICS) is None:
        consent_service.set_consent(
            shopper_id=shopper_id,
            purpose=ConsentPurpose.PRODUCT_ANALYTICS,
            granted=True,
            source="default",
        )


@router.put("/products/{product_id}/reaction", response_model=ReactionResponse)
async def set_product_reaction(
    product_id: str,
    payload: ReactionUpdateRequest,
    principal: Principal = Depends(get_principal),
    repo: InMemoryFeedbackRepository = Depends(get_feedback_repository),
    consent_service: FeedbackConsentService = Depends(get_feedback_consent_service),
    ranking_service: PersonalizedRankingService = Depends(get_ranking_service),
) -> ReactionResponse:
    """Set the shopper's current reaction (LIKE, DISLIKE, NONE) idempotently."""
    shopper_id = str(principal.user_id)
    _ensure_personalized_consent_or_default(consent_service, shopper_id)
    current = repo.get_reaction(shopper_id, product_id)
    if payload.reaction == ReactionState.LIKE:
        ev_type = FeedbackEventType.PRODUCT_LIKED.value
    elif payload.reaction == ReactionState.DISLIKE:
        ev_type = FeedbackEventType.PRODUCT_DISLIKED.value
    elif current == ReactionState.DISLIKE:
        ev_type = FeedbackEventType.PRODUCT_DISLIKE_REMOVED.value
    else:
        ev_type = FeedbackEventType.PRODUCT_LIKE_REMOVED.value

    ingestion = FeedbackIngestionService(repository=repo, consent_service=consent_service)
    processor = FeedbackProcessor(repository=repo, consent_service=consent_service)
    try:
        ev_req = FeedbackEventRequest(
            event_id=payload.idempotency_key,
            event_type=ev_type,
            subject_type="PRODUCT",
            subject_id=product_id,
            occurred_at=datetime.now(UTC),
            source="api",
        )
        stored, _ = ingestion.ingest(shopper_id=shopper_id, request=ev_req)
        processor.process_event(stored.event_id)
        ranking_service.cache.invalidate_shopper(shopper_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except FeedbackConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return ReactionResponse(product_id=product_id, reaction=repo.get_reaction(shopper_id, product_id))


@router.get("/products/{product_id}/reaction", response_model=ReactionResponse)
async def get_product_reaction(
    product_id: str,
    principal: Principal = Depends(get_principal),
    repo: InMemoryFeedbackRepository = Depends(get_feedback_repository),
) -> ReactionResponse:
    """Retrieve the authenticated shopper's current reaction for a product."""
    return ReactionResponse(
        product_id=product_id,
        reaction=repo.get_reaction(str(principal.user_id), product_id),
        status="CURRENT",
    )


@router.put("/products/{product_id}/saved", response_model=SavedProductResponse)
async def save_product(
    product_id: str,
    payload: SaveProductRequest,
    principal: Principal = Depends(get_principal),
    repo: InMemoryFeedbackRepository = Depends(get_feedback_repository),
    consent_service: FeedbackConsentService = Depends(get_feedback_consent_service),
    ranking_service: PersonalizedRankingService = Depends(get_ranking_service),
) -> SavedProductResponse:
    """Save a product idempotently for the authenticated shopper."""
    shopper_id = str(principal.user_id)
    _ensure_personalized_consent_or_default(consent_service, shopper_id)
    ingestion = FeedbackIngestionService(repository=repo, consent_service=consent_service)
    processor = FeedbackProcessor(repository=repo, consent_service=consent_service)
    try:
        ev_req = FeedbackEventRequest(
            event_id=payload.idempotency_key,
            event_type=FeedbackEventType.PRODUCT_SAVED.value,
            subject_type="PRODUCT",
            subject_id=product_id,
            occurred_at=datetime.now(UTC),
            source="api",
            context=(
                {"merchant_offer_id": payload.merchant_offer_id}
                if payload.merchant_offer_id
                else {}
            ),
        )
        stored, _ = ingestion.ingest(shopper_id=shopper_id, request=ev_req)
        processor.process_event(stored.event_id)
        ranking_service.cache.invalidate_shopper(shopper_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except FeedbackConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    saved = repo.get_saved(shopper_id, product_id)
    assert saved is not None
    return SavedProductResponse(
        product_id=product_id,
        merchant_offer_id=saved.merchant_offer_id,
        is_saved=saved.is_saved,
        saved_at=saved.saved_at,
        updated_at=saved.updated_at,
    )


@router.delete("/products/{product_id}/saved", response_model=SavedProductResponse)
async def unsave_product(
    product_id: str,
    principal: Principal = Depends(get_principal),
    repo: InMemoryFeedbackRepository = Depends(get_feedback_repository),
    consent_service: FeedbackConsentService = Depends(get_feedback_consent_service),
    ranking_service: PersonalizedRankingService = Depends(get_ranking_service),
) -> SavedProductResponse:
    """Remove saved state for a product idempotently."""
    shopper_id = str(principal.user_id)
    _ensure_personalized_consent_or_default(consent_service, shopper_id)
    ingestion = FeedbackIngestionService(repository=repo, consent_service=consent_service)
    processor = FeedbackProcessor(repository=repo, consent_service=consent_service)
    ev_req = FeedbackEventRequest(
        event_id=uuid4(),
        event_type=FeedbackEventType.PRODUCT_UNSAVED.value,
        subject_type="PRODUCT",
        subject_id=product_id,
        occurred_at=datetime.now(UTC),
        source="api",
    )
    stored, _ = ingestion.ingest(shopper_id=shopper_id, request=ev_req)
    processor.process_event(stored.event_id)
    ranking_service.cache.invalidate_shopper(shopper_id)
    saved = repo.get_saved(shopper_id, product_id)
    assert saved is not None
    return SavedProductResponse(
        product_id=product_id,
        merchant_offer_id=saved.merchant_offer_id,
        is_saved=saved.is_saved,
        saved_at=saved.saved_at,
        updated_at=saved.updated_at,
    )


@router.get("/products/{product_id}/saved", response_model=SavedProductResponse)
async def get_saved_product(
    product_id: str,
    principal: Principal = Depends(get_principal),
    repo: InMemoryFeedbackRepository = Depends(get_feedback_repository),
) -> SavedProductResponse:
    """Read current saved state for a product."""
    saved = repo.get_saved(str(principal.user_id), product_id)
    if saved is None:
        return SavedProductResponse(
            product_id=product_id,
            is_saved=False,
            updated_at=datetime.now(UTC),
        )
    return SavedProductResponse(
        product_id=product_id,
        merchant_offer_id=saved.merchant_offer_id,
        is_saved=saved.is_saved,
        saved_at=saved.saved_at,
        updated_at=saved.updated_at,
    )


@router.post(
    "/feedback/events",
    response_model=FeedbackEventResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_feedback_event(
    request: FeedbackEventRequest,
    principal: Principal = Depends(get_principal),
    repo: InMemoryFeedbackRepository = Depends(get_feedback_repository),
    consent_service: FeedbackConsentService = Depends(get_feedback_consent_service),
    ranking_service: PersonalizedRankingService = Depends(get_ranking_service),
) -> FeedbackEventResponse:
    """Ingest a feedback or interaction event with idempotency and consent checks."""
    shopper_id = str(principal.user_id)
    _ensure_personalized_consent_or_default(consent_service, shopper_id)
    ingestion = FeedbackIngestionService(repository=repo, consent_service=consent_service)
    processor = FeedbackProcessor(repository=repo, consent_service=consent_service)
    try:
        stored, deduplicated = ingestion.ingest(shopper_id=shopper_id, request=request)
        if not deduplicated:
            processor.process_event(stored.event_id)
            ranking_service.cache.invalidate_shopper(shopper_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except FeedbackConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return FeedbackEventResponse(
        event_id=stored.event_id,
        status=stored.processing_status,
        received_at=stored.received_at,
        deduplicated=deduplicated,
    )


@router.post(
    "/tryon/jobs/{job_id}/feedback",
    response_model=VTOQualityFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_vto_quality_feedback(
    job_id: str,
    payload: VTOQualityFeedbackRequest,
    principal: Principal = Depends(get_principal),
    repo: InMemoryFeedbackRepository = Depends(get_feedback_repository),
    consent_service: FeedbackConsentService = Depends(get_feedback_consent_service),
) -> VTOQualityFeedbackResponse:
    """Submit VTO visual quality feedback without polluting product preference."""
    shopper_id = str(principal.user_id)
    _ensure_personalized_consent_or_default(consent_service, shopper_id)
    ingestion = FeedbackIngestionService(repository=repo, consent_service=consent_service)
    try:
        ev_req = FeedbackEventRequest(
            event_id=payload.event_id or uuid4(),
            event_type=FeedbackEventType.VTO_QUALITY_FEEDBACK_SUBMITTED.value,
            subject_type="VTO_JOB",
            subject_id=job_id,
            occurred_at=datetime.now(UTC),
            source="api",
            context={
                "rating": payload.rating.value,
                "issue_codes": payload.issue_codes,
                "comment": payload.comment or "",
            },
        )
        stored, _ = ingestion.ingest(shopper_id=shopper_id, request=ev_req)
        repo.vto_quality_feedback[(shopper_id, job_id)] = {
            "rating": payload.rating.value,
            "issue_codes": list(payload.issue_codes),
            "event_id": str(stored.event_id),
        }
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except FeedbackConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return VTOQualityFeedbackResponse(
        job_id=job_id,
        rating=payload.rating,
        issue_codes=payload.issue_codes,
    )


@router.post(
    "/merchant-offers/{offer_id}/outbound",
    response_model=OutboundClickResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_merchant_outbound(
    offer_id: str,
    payload: OutboundClickRequest,
    principal: Principal = Depends(get_principal),
    repo: InMemoryFeedbackRepository = Depends(get_feedback_repository),
    consent_service: FeedbackConsentService = Depends(get_feedback_consent_service),
) -> OutboundClickResponse:
    """Record a merchant outbound redirect intent event (never reported as a purchase)."""
    shopper_id = str(principal.user_id)
    _ensure_personalized_consent_or_default(consent_service, shopper_id)
    redirect_id = f"redir_{uuid4().hex[:16]}"
    ingestion = FeedbackIngestionService(repository=repo, consent_service=consent_service)
    processor = FeedbackProcessor(repository=repo, consent_service=consent_service)
    try:
        ev_req = FeedbackEventRequest(
            event_id=payload.event_id or uuid4(),
            event_type=FeedbackEventType.MERCHANT_OUTBOUND_CLICKED.value,
            subject_type="MERCHANT_OFFER",
            subject_id=offer_id,
            occurred_at=datetime.now(UTC),
            source="api",
            context={
                "product_id": payload.product_id,
                "redirect_id": redirect_id,
                "surface_source": payload.source,
            },
        )
        stored, _ = ingestion.ingest(shopper_id=shopper_id, request=ev_req)
        processor.process_event(stored.event_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except FeedbackConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return OutboundClickResponse(
        redirect_id=redirect_id,
        merchant_offer_id=offer_id,
        product_id=payload.product_id,
    )


@router.get("/feedback/consents", response_model=list[ConsentStateResponse])
async def list_feedback_consents(
    principal: Principal = Depends(get_principal),
    consent_service: FeedbackConsentService = Depends(get_feedback_consent_service),
) -> list[ConsentStateResponse]:
    """List current purpose-specific feedback/personalization consents."""
    entries = consent_service.list_consents(str(principal.user_id))
    return [
        ConsentStateResponse(
            purpose=e.purpose,
            status=e.status,
            policy_version=e.policy_version,
            revision=e.revision,
            recorded_at=e.recorded_at,
            withdrawn_at=e.withdrawn_at,
        )
        for e in entries
    ]


@router.put("/feedback/consents/{purpose}", response_model=ConsentStateResponse)
async def update_feedback_consent(
    purpose: ConsentPurpose,
    payload: ConsentUpdateRequest,
    principal: Principal = Depends(get_principal),
    repo: InMemoryFeedbackRepository = Depends(get_feedback_repository),
    consent_service: FeedbackConsentService = Depends(get_feedback_consent_service),
    ranking_service: PersonalizedRankingService = Depends(get_ranking_service),
) -> ConsentStateResponse:
    """Grant or withdraw a purpose-specific consent; withdrawal clears caches & projections."""
    shopper_id = str(principal.user_id)
    entry = consent_service.set_consent(
        shopper_id=shopper_id,
        purpose=purpose,
        granted=payload.granted,
        policy_version=payload.policy_version,
        source=payload.source,
    )
    if purpose == ConsentPurpose.PERSONALIZED_RANKING and not payload.granted:
        ranking_service.cache.invalidate_shopper(shopper_id)
        repo.clear_personalization_projections(shopper_id)

    return ConsentStateResponse(
        purpose=entry.purpose,
        status=entry.status,
        policy_version=entry.policy_version,
        revision=entry.revision,
        recorded_at=entry.recorded_at,
        withdrawn_at=entry.withdrawn_at,
    )


@router.delete("/shopper/preferences")
async def reset_personalization_preferences(
    principal: Principal = Depends(get_principal),
    repo: InMemoryFeedbackRepository = Depends(get_feedback_repository),
    ranking_service: PersonalizedRankingService = Depends(get_ranking_service),
) -> dict[str, object]:
    """Clear shopper personalization projections and invalidate ranking cache."""
    shopper_id = str(principal.user_id)
    repo.clear_personalization_projections(shopper_id)
    ranking_service.cache.invalidate_shopper(shopper_id)
    return {"shopper_id": shopper_id, "status": "reset"}


@router.get("/feedback/metrics")
async def get_feedback_metrics(
    _principal: Principal = Depends(get_principal),
    repo: InMemoryFeedbackRepository = Depends(get_feedback_repository),
) -> dict[str, object]:
    """Read feedback ingestion, bias, and personalization coverage metrics."""
    return asdict(compute_feedback_monitoring(repo))
