from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.commerce_wardrobe.application.create_buy_click import (
    CreateBuyClickCommand,
    CreateBuyClickUseCase,
)
from fashx.commerce_wardrobe.application.list_wardrobe import (
    ListWardrobeUseCase,
    WardrobeItemView,
)
from fashx.commerce_wardrobe.application.mark_purchased import (
    MarkPurchasedCommand,
    MarkPurchasedUseCase,
)
from fashx.commerce_wardrobe.application.remove_from_wardrobe import (
    RemoveFromWardrobeUseCase,
)
from fashx.commerce_wardrobe.application.save_to_wardrobe import (
    SaveToWardrobeCommand,
    SaveToWardrobeUseCase,
)
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
from fashx.core.database import get_session_factory
from fashx.core.dependencies import get_storage
from fashx.core.errors import ConflictError, EntityNotFoundError
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork
from fashx.security.deps import Principal, get_principal
from fashx.security.errors import forbidden
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
    garment_id: UUID
    user_id: UUID | None = None
    offer_id: UUID | None = None


class BuyClickResponse(BaseModel):
    buy_click_id: UUID
    redirect_url: str
    tracking_id: str


class FitFeedbackRequest(BaseModel):
    item_id: UUID | None = None
    user_id: UUID | None = None
    garment_id: UUID | None = None
    brand_id: UUID | None = None
    category: str | None = None
    size_label: str = "M"
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
    principal: Principal = Depends(get_principal),
    wardrobe_uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
    profile_uow: ProfileUnitOfWork = Depends(get_profile_uow),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> SaveWardrobeResponse:
    """Save a garment to virtual closet with immutable snapshot metadata (Rule I11)."""
    if str(request.user_id) != principal.user_id:
        raise forbidden("Forbidden: user_id mismatch")

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
    principal: Principal = Depends(get_principal),
    wardrobe_uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
    storage: Any = Depends(get_storage),
) -> list[WardrobeItemView]:
    """Retrieve items in user's virtual closet."""
    if str(user_id) != principal.user_id:
        raise forbidden("Forbidden: user_id mismatch")

    uc = ListWardrobeUseCase(wardrobe_uow, catalog_uow=catalog_uow, storage=storage)
    return await uc.execute(user_id, limit=limit, offset=offset)


class MarkPurchasedRequest(BaseModel):
    purchased: bool = True


@router.patch("/wardrobe/items/{item_id}", response_model=WardrobeItemView)
async def mark_purchased(
    item_id: UUID,
    request: MarkPurchasedRequest,
    principal: Principal = Depends(get_principal),
    wardrobe_uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
    storage: Any = Depends(get_storage),
) -> WardrobeItemView:
    """Mark a wardrobe item as purchased (scoped to owner)."""
    caller_user_id = UUID(principal.user_id)
    uc = MarkPurchasedUseCase(wardrobe_uow)
    await uc.execute(
        MarkPurchasedCommand(
            user_id=caller_user_id,
            item_id=item_id,
            purchased=request.purchased,
        )
    )

    list_uc = ListWardrobeUseCase(wardrobe_uow, catalog_uow=catalog_uow, storage=storage)
    items = await list_uc.execute(caller_user_id)
    for it in items:
        if it.id == item_id:
            return it
    raise EntityNotFoundError("WardrobeItem", item_id)


@router.delete("/wardrobe/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_wardrobe(
    item_id: UUID,
    user_id: UUID | None = Query(default=None),
    principal: Principal = Depends(get_principal),
    wardrobe_uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
) -> None:
    """Remove item from virtual closet."""
    caller_user_id = UUID(principal.user_id)
    if user_id is not None and user_id != caller_user_id:
        raise forbidden("Forbidden: user_id mismatch")

    uc = RemoveFromWardrobeUseCase(wardrobe_uow)
    await uc.execute(caller_user_id, item_id)


# --- Endpoints: Commerce Outbound ---


@router.post(
    "/commerce/buy-clicks",
    response_model=BuyClickResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_buy_click(
    request: BuyClickRequest,
    principal: Principal = Depends(get_principal),
    commerce_uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
    profile_uow: ProfileUnitOfWork = Depends(get_profile_uow),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> BuyClickResponse:
    """Generate affiliate-tracked outbound redirect URL (Rule I12)."""
    effective_user_id = UUID(principal.user_id)
    if request.user_id is not None and request.user_id != effective_user_id:
        raise forbidden("Forbidden: user_id mismatch")

    effective_offer_id = request.offer_id
    if effective_offer_id is None:
        async with catalog_uow:
            offers = await catalog_uow.offers.list_for_garment(request.garment_id)
            if not offers:
                from fashx.core.errors import EntityNotFoundError

                raise EntityNotFoundError("MerchantOffer", request.garment_id)
            effective_offer_id = offers[0].id

    uc = CreateBuyClickUseCase(commerce_uow, profile_uow, catalog_uow)
    res = await uc.execute(
        CreateBuyClickCommand(
            user_id=effective_user_id,
            garment_id=request.garment_id,
            offer_id=effective_offer_id,
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
    principal: Principal = Depends(get_principal),
    uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
    catalog_uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> FitFeedbackResponse:
    """Record granular post-purchase fit feedback and update sizing calibration (Rule I13)."""
    caller_user_id = UUID(principal.user_id)
    if request.user_id is not None and request.user_id != caller_user_id:
        raise forbidden("Forbidden: user_id mismatch")

    if request.item_id is not None:
        async with uow:
            item = await uow.wardrobe.get_by_id_and_user(request.item_id, caller_user_id)
            if item is None:
                raise EntityNotFoundError("WardrobeItem", request.item_id)

            existing = await uow.fit_feedback.get_by_user_and_garment(
                caller_user_id, item.garment_id
            )
            if existing is not None:
                raise ConflictError("Fit feedback already submitted for this item")

        async with catalog_uow:
            garment = await catalog_uow.canonical_garments.get_by_id(item.garment_id)
            if garment is None:
                raise EntityNotFoundError("CanonicalGarment", item.garment_id)
            garment_id = garment.id
            brand_id = garment.brand_id
            if brand_id is None:
                offers = await catalog_uow.offers.list_for_garment(garment.id)
                if offers:
                    prod = await catalog_uow.merchant_products.get_by_source_id(
                        offers[0].merchant_id, offers[0].source_product_id
                    )
                    if prod and prod.brand_id:
                        brand_id = prod.brand_id
            if brand_id is None:
                from database.models.catalog import Brand

                brand_stmt = select(Brand).limit(1)
                first_brand = (await catalog_uow.session.scalars(brand_stmt)).first()
                if first_brand:
                    brand_id = first_brand.id
                else:
                    new_b = Brand(name="Default Brand", normalized_name="default_brand")
                    catalog_uow.session.add(new_b)
                    await catalog_uow.session.flush()
                    brand_id = new_b.id
            category = garment.category or "apparel"
    else:
        if request.garment_id is None or request.brand_id is None or request.category is None:
            from fashx.core.errors import ValidationError

            raise ValidationError(
                "garment_id, brand_id, and category are required when item_id is not provided"
            )
        garment_id = request.garment_id
        brand_id = request.brand_id
        category = request.category

    uc = SubmitFitFeedbackUseCase(uow)
    res = await uc.execute(
        SubmitFitFeedbackCommand(
            user_id=caller_user_id,
            garment_id=garment_id,
            brand_id=brand_id,
            category=category,
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
    principal: Principal = Depends(get_principal),
    uow: CommerceWardrobeUnitOfWork = Depends(get_commerce_uow),
) -> TryOnFeedbackResponse:
    """Record user try-on visual realism and purchase confidence (Rule I14)."""
    if str(request.user_id) != principal.user_id:
        raise forbidden("Forbidden: user_id mismatch")

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
