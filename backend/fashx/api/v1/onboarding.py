from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.core.database import get_session_factory
from fashx.security.deps import Principal, get_principal
from fashx.security.errors import unauthorized

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def get_catalog_uow() -> CatalogUnitOfWork:
    return CatalogUnitOfWork(get_session_factory())


class StyleQuizItem(BaseModel):
    id: UUID
    title: str
    category: str
    subcategory: str | None = None
    image_url: str | None = None
    tags: list[str] = []


class StyleQuizResponse(BaseModel):
    garments: list[StyleQuizItem]


MIN_QUIZ_PICKS = 3
MAX_QUIZ_PICKS = 10


class StyleQuizPickInput(BaseModel):
    garment_id: UUID
    liked: bool


class SubmitStyleQuizPicksRequest(BaseModel):
    picks: list[StyleQuizPickInput] = Field(
        ..., min_length=MIN_QUIZ_PICKS, max_length=MAX_QUIZ_PICKS
    )


class SubmitStyleQuizPicksResponse(BaseModel):
    user_id: str
    saved_count: int
    status: str = "recorded"


# Seed garments if database catalog is freshly initialized
DEFAULT_SEED_GARMENTS = [
    {
        "id": UUID("00000000-0000-0000-0000-000000000001"),
        "title": "Tailored Oxford Shirt",
        "category": "tops",
        "subcategory": "formal_shirts",
        "image_url": "https://media.fashx.studio/catalog/garments/seed_oxford.jpg",
        "tags": ["classic", "formal", "office", "minimal"],
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000002"),
        "title": "Urban Oversized Hoodie",
        "category": "tops",
        "subcategory": "sweatshirts",
        "image_url": "https://media.fashx.studio/catalog/garments/seed_hoodie.jpg",
        "tags": ["streetwear", "casual", "cozy", "trendy"],
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000003"),
        "title": "Minimalist Linen Trousers",
        "category": "bottoms",
        "subcategory": "trousers",
        "image_url": "https://media.fashx.studio/catalog/garments/seed_trousers.jpg",
        "tags": ["minimal", "summer", "breathable", "smart_casual"],
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000004"),
        "title": "Evening Midi Dress",
        "category": "dresses",
        "subcategory": "evening_dresses",
        "image_url": "https://media.fashx.studio/catalog/garments/seed_dress.jpg",
        "tags": ["elegant", "party", "cocktail", "feminine"],
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000005"),
        "title": "Vintage Wash Denim Jacket",
        "category": "outerwear",
        "subcategory": "jackets",
        "image_url": "https://media.fashx.studio/catalog/garments/seed_denim.jpg",
        "tags": ["vintage", "denim", "layering", "casual"],
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000006"),
        "title": "Seamless Athleisure Tee",
        "category": "activewear",
        "subcategory": "t_shirts",
        "image_url": "https://media.fashx.studio/catalog/garments/seed_active.jpg",
        "tags": ["sporty", "gym", "flexible", "breathable"],
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000007"),
        "title": "Silk Slip Skirt",
        "category": "bottoms",
        "subcategory": "skirts",
        "image_url": "https://media.fashx.studio/catalog/garments/seed_skirt.jpg",
        "tags": ["chic", "summer", "versatile", "luxe"],
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000008"),
        "title": "Double-Breasted Wool Blazer",
        "category": "outerwear",
        "subcategory": "blazers",
        "image_url": "https://media.fashx.studio/catalog/garments/seed_blazer.jpg",
        "tags": ["tailored", "power_dressing", "autumn", "classic"],
    },
]


@router.get("/style-quiz", response_model=StyleQuizResponse)
async def get_style_quiz(
    principal: Principal = Depends(get_principal),
    uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> StyleQuizResponse:
    """Fetch 6-12 seed garments for the cold-start onboarding style quiz."""
    async with uow:
        garments = await uow.canonical_garments.list(limit=12)
        if not garments:
            return StyleQuizResponse(
                garments=[StyleQuizItem(**item) for item in DEFAULT_SEED_GARMENTS]
            )

        items: list[StyleQuizItem] = []
        for g in garments:
            images = await uow.images.list_for_garment(g.id)
            img_url = images[0].image_url if images else None
            enrichment = await uow.enrichments.get_by_garment_id(g.id)
            tags = []
            if enrichment and enrichment.attributes_json:
                tags = enrichment.attributes_json.get("tags", [])
                if not tags:
                    tags = [g.category]
                    if g.subcategory:
                        tags.append(g.subcategory)

            title = g.display_name or f"{g.category.capitalize()} {g.subcategory or ''}".strip()
            items.append(
                StyleQuizItem(
                    id=g.id,
                    title=title,
                    category=g.category,
                    subcategory=g.subcategory,
                    image_url=img_url,
                    tags=tags,
                )
            )

        return StyleQuizResponse(garments=items)


def principal_user_uuid(principal: Principal) -> UUID:
    try:
        return UUID(principal.user_id)
    except (ValueError, TypeError, AttributeError):
        raise unauthorized("Authenticated identity has an invalid user ID")


@router.post(
    "/style-quiz/picks",
    response_model=SubmitStyleQuizPicksResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_style_quiz_picks(
    payload: SubmitStyleQuizPicksRequest,
    principal: Principal = Depends(get_principal),
    uow: CatalogUnitOfWork = Depends(get_catalog_uow),
) -> SubmitStyleQuizPicksResponse:
    """Record customer style preference picks from the onboarding quiz."""
    user_uuid = principal_user_uuid(principal)

    saved = 0
    async with uow:
        for pick in payload.picks:
            await uow.style_quiz_picks.upsert_pick(
                user_id=user_uuid,
                garment_id=pick.garment_id,
                liked=pick.liked,
            )
            saved += 1
        await uow.commit()

    return SubmitStyleQuizPicksResponse(
        user_id=principal.user_id,
        saved_count=saved,
        status="recorded",
    )
