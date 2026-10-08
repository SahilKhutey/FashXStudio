from uuid import UUID

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.commerce_wardrobe.application.create_buy_click import (
    CreateBuyClickCommand,
    CreateBuyClickUseCase,
)
from api.app.commerce_wardrobe.application.list_wardrobe import (
    ListWardrobeUseCase,
    WardrobeItemView,
)
from api.app.commerce_wardrobe.application.remove_from_wardrobe import (
    RemoveFromWardrobeUseCase,
)
from api.app.commerce_wardrobe.application.save_to_wardrobe import (
    SaveToWardrobeCommand,
    SaveToWardrobeUseCase,
)
from api.app.commerce_wardrobe.application.submit_fit_feedback import (
    SubmitFitFeedbackCommand,
    SubmitFitFeedbackUseCase,
)
from api.app.commerce_wardrobe.application.submit_tryon_feedback import (
    SubmitTryOnFeedbackCommand,
    SubmitTryOnFeedbackUseCase,
)
from api.app.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from api.app.core.database import get_session_factory
from api.app.profile.repositories.profile_repository import ProfileUnitOfWork
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from schemas.common.enums import FitVerdict, VisualAccuracy

router = APIRouter(tags=["commerce-wardrobe-feedback"])


def get_commerce_uow() -> CommerceWardrobeUnitOfWork:
    return CommerceWardrobeUnitOfWork(get_session_factory())


def get_profile_uow() -> ProfileUnitOfWork:
    return ProfileUnitOfWork(get_session_factory())


def get_catalog_uow() -> CatalogUnitOfWork:
    return CatalogUnitOfWork(get_session_factory())


# --- Schemas ---


class SaveWardrobeRequest(BaseModel):
    user_id: UUID
    garment_id: UUID
    offer_id: UUID | None = None
    tryon_artifact_id: UUID | None = None


class SaveWardrobeResponse(BaseModel):
    item_id: UUID
    user_id: UUID
    garment_id: UUID
    snapshot_title: str
    snapshot_price_minor: int
    snapshot_currency: str
    snapshot_image_key: str
    tryon_artifact_id: UUID | None


class BuyClickRequest(BaseModel):
    user_id: UUID
    garment_id: UUID
    offer_id: UUID


class BuyClickResponse(BaseModel):
    buy_click_id: UUID
    redirect_url: str
    tracking_id: str


class FitFeedbackRequest(BaseModel):
    user_id: UUID
    garment_id: UUID
    brand_id: UUID
    category: str
    size_label: str
    verdict: FitVerdict
    fit_type: str | None = None
    buy_click_id: UUID | None = None


class FitFeedbackResponse(BaseModel):
    feedback_id: UUID
    user_id: UUID
    brand_id: UUID
    verdict: str
    brand_bias_score: float
    brand_recommendation: str
    total_observations: int


class TryOnFeedbackRequest(BaseModel):
    user_id: UUID
    tryon_job_id: UUID
    visual_accuracy: VisualAccuracy
    purchase_confidence: int | None = Field(default=None, ge=1, le=5)


class TryOnFeedbackResponse(BaseModel):
    feedback_id: UUID
    user_id: UUID
    tryon_job_id: UUID
    visual_accuracy: str
    purchase_confidence: int | None


class BrandCalibrationResponse(BaseModel):
    brand_id: UUID
    category: str | None
    total_observations: int
    bias_score: float
    recommendation: str
    too_tight_pct: float
    true_to_size_pct: float
    too_loose_pct: float


# --- Endpoints: Wardrobe ---


@router.post(
    "/wardrobe/items",
    response_model=SaveWardrobeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_to_wardrobe(
    request: SaveWardrobeRequest,
    wardrobe_uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
    profile_uow: ProfileUnitOfWork = Depends(get_profile_uow),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> SaveWardrobeResponse:
    """Save a garment to virtual closet with immutable snapshot metadata (Rule I11)."""
    uc = SaveToWardrobeUseCase(wardrobe_uow, profile_uow, catalog_uow)
    res = await uc.execute(
        SaveToWardrobeCommand(
            user_id=request.user_id,
            garment_id=request.garment_id,
            offer_id=request.offer_id,
            tryon_artifact_id=request.tryon_artifact_id,
        )
    )
    return SaveWardrobeResponse(
        item_id=res.item_id,
        user_id=res.user_id,
        garment_id=res.garment_id,
        snapshot_title=res.snapshot_title,
        snapshot_price_minor=res.snapshot_price_minor,
        snapshot_currency=res.snapshot_currency,
        snapshot_image_key=res.snapshot_image_key,
        tryon_artifact_id=res.tryon_artifact_id,
    )


@router.get("/wardrobe/users/{user_id}", response_model=list[WardrobeItemView])
async def list_user_wardrobe(
    user_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    wardrobe_uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
) -> list[WardrobeItemView]:
    """Retrieve items in user's virtual closet."""
    uc = ListWardrobeUseCase(wardrobe_uow)
    return await uc.execute(user_id, limit=limit, offset=offset)


@router.delete("/wardrobe/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_wardrobe(
    item_id: UUID,
    user_id: UUID = Query(...),
    wardrobe_uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
) -> None:
    """Remove item from virtual closet."""
    uc = RemoveFromWardrobeUseCase(wardrobe_uow)
    await uc.execute(user_id, item_id)


# --- Endpoints: Commerce Outbound ---


@router.post(
    "/commerce/buy-clicks",
    response_model=BuyClickResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_buy_click(
    request: BuyClickRequest,
    commerce_uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
    profile_uow: ProfileUnitOfWork = Depends(get_profile_uow),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> BuyClickResponse:
    """Generate affiliate-tracked outbound redirect URL (Rule I12)."""
    uc = CreateBuyClickUseCase(commerce_uow, profile_uow, catalog_uow)
    res = await uc.execute(
        CreateBuyClickCommand(
            user_id=request.user_id,
            garment_id=request.garment_id,
            offer_id=request.offer_id,
        )
    )
    return BuyClickResponse(
        buy_click_id=res.buy_click_id,
        redirect_url=res.redirect_url,
        tracking_id=res.tracking_id,
    )


# --- Endpoints: Feedback & Fit Learning ---


@router.post(
    "/feedback/fit",
    response_model=FitFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_fit_feedback(
    request: FitFeedbackRequest,
    uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
) -> FitFeedbackResponse:
    """Record granular post-purchase fit feedback and update sizing calibration (Rule I13)."""
    uc = SubmitFitFeedbackUseCase(uow)
    res = await uc.execute(
        SubmitFitFeedbackCommand(
            user_id=request.user_id,
            garment_id=request.garment_id,
            brand_id=request.brand_id,
            category=request.category,
            size_label=request.size_label,
            verdict=request.verdict.value,
            fit_type=request.fit_type,
            buy_click_id=request.buy_click_id,
        )
    )
    return FitFeedbackResponse(
        feedback_id=res.feedback_id,
        user_id=res.user_id,
        brand_id=res.brand_id,
        verdict=res.verdict,
        brand_bias_score=res.brand_bias_score,
        brand_recommendation=res.brand_recommendation,
        total_observations=res.total_observations,
    )


@router.get(
    "/feedback/brands/{brand_id}/calibration",
    response_model=BrandCalibrationResponse,
)
async def get_brand_calibration(
    brand_id: UUID,
    category: str | None = Query(default=None),
    uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
) -> BrandCalibrationResponse:
    """Query current brand sizing bias and recommendation (size up, true to size, size down)."""
    async with uow:
        metrics = await uow.fit_feedback.compute_brand_bias(brand_id, category)
        return BrandCalibrationResponse(
            brand_id=brand_id,
            category=category,
            total_observations=int(metrics["total_observations"]),
            bias_score=float(metrics["bias_score"]),
            recommendation=str(metrics["recommendation"]),
            too_tight_pct=float(metrics["too_tight_pct"]),
            true_to_size_pct=float(metrics["true_to_size_pct"]),
            too_loose_pct=float(metrics["too_loose_pct"]),
        )


@router.post(
    "/feedback/tryon",
    response_model=TryOnFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_tryon_feedback(
    request: TryOnFeedbackRequest,
    uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
) -> TryOnFeedbackResponse:
    """Record user try-on visual realism and purchase confidence (Rule I14)."""
    uc = SubmitTryOnFeedbackUseCase(uow)
    res = await uc.execute(
        SubmitTryOnFeedbackCommand(
            user_id=request.user_id,
            tryon_job_id=request.tryon_job_id,
            visual_accuracy=request.visual_accuracy.value,
            purchase_confidence=request.purchase_confidence,
        )
    )
    return TryOnFeedbackResponse(
        feedback_id=res.feedback_id,
        user_id=res.user_id,
        tryon_job_id=res.tryon_job_id,
        visual_accuracy=res.visual_accuracy,
        purchase_confidence=res.purchase_confidence,
    )
