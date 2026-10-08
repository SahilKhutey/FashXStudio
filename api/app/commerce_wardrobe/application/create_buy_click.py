from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from uuid import UUID, uuid4

from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from api.app.core.errors import EntityNotFoundError
from api.app.profile.repositories.profile_repository import ProfileUnitOfWork
from database.models.commerce_feedback import BuyClick


@dataclass(frozen=True)
class CreateBuyClickCommand:
    user_id: UUID
    garment_id: UUID
    offer_id: UUID


@dataclass(frozen=True)
class CreateBuyClickResult:
    buy_click_id: UUID
    redirect_url: str
    tracking_id: str


class CreateBuyClickUseCase:
    """Orchestrates outbound merchant purchase redirects and affiliate attribution tracking (Rule I12)."""

    def __init__(
        self,
        commerce_uow: CommerceWardrobeUnitOfWork,
        profile_uow: ProfileUnitOfWork,
        catalog_uow: CatalogUnitOfWork,
    ) -> None:
        self.commerce_uow = commerce_uow
        self.profile_uow = profile_uow
        self.catalog_uow = catalog_uow

    async def execute(self, cmd: CreateBuyClickCommand) -> CreateBuyClickResult:
        # 1. Validate User
        async with self.profile_uow:
            user = await self.profile_uow.users.get_by_id(cmd.user_id)
            if user is None:
                raise EntityNotFoundError("User", cmd.user_id)

        # 2. Retrieve Merchant Offer and Destination URL
        async with self.catalog_uow:
            offer = await self.catalog_uow.offers.get_by_id(cmd.offer_id)
            if offer is None:
                raise EntityNotFoundError("MerchantOffer", cmd.offer_id)

            product = await self.catalog_uow.merchant_products.get_by_source_id(
                offer.merchant_id, offer.source_product_id
            )
            raw_destination_url = product.source_url if product else "https://fashx.studio/shop"

        # 3. Generate Tracking ID & Record Click
        tracking_id = f"fashx_{cmd.user_id.hex[:8]}_{uuid4().hex[:10]}"
        async with self.commerce_uow:
            click = BuyClick(
                user_id=cmd.user_id,
                garment_id=cmd.garment_id,
                offer_id=cmd.offer_id,
                affiliate_network="fashx_direct",
                tracking_id=tracking_id,
            )
            self.commerce_uow.buy_clicks.add(click)
            await self.commerce_uow.commit()
            click_id = click.id

        # 4. Construct Attribution URL with sub_id and UTM parameters
        parsed = urlparse(raw_destination_url)
        query_params = dict(parse_qsl(parsed.query))
        query_params["utm_source"] = "fashx"
        query_params["utm_medium"] = "app"
        query_params["utm_campaign"] = "vto_purchase"
        query_params["sub_id"] = tracking_id
        query_params["click_id"] = str(click_id)

        enriched_query = urlencode(query_params)
        redirect_url = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                enriched_query,
                parsed.fragment,
            )
        )

        return CreateBuyClickResult(
            buy_click_id=click_id,
            redirect_url=redirect_url,
            tracking_id=tracking_id,
        )
