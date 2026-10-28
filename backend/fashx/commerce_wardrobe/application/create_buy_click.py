from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from uuid import UUID, uuid4

from database.models.commerce_feedback import BuyClick
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from fashx.commerce_wardrobe.repositories.commerce_wardrobe_repository import (
    CommerceWardrobeUnitOfWork,
)
from fashx.core.errors import EntityNotFoundError, ValidationError
from fashx.profile.repositories.profile_repository import ProfileUnitOfWork


def validate_retailer_url(
    raw_url: str,
    allowed_hosts: set[str] | None = None,
) -> str:
    """Validates that a retailer destination uses HTTPS, has no credentials, and belongs to an approved host."""
    if not raw_url:
        raise ValidationError("Retailer URL must not be empty", field="redirect_url")

    parsed = urlparse(raw_url)
    if parsed.scheme != "https":
        raise ValidationError("Retailer URL must use HTTPS", field="redirect_url")

    if not parsed.hostname:
        raise ValidationError("Retailer URL has no valid hostname", field="redirect_url")

    hostname = parsed.hostname.lower()
    if parsed.username or parsed.password:
        raise ValidationError("Credentials are not permitted in retailer URLs", field="redirect_url")

    if allowed_hosts:
        normalized_allowed = {h.lower() for h in allowed_hosts}
        matched = any(
            hostname == h or hostname.endswith("." + h)
            for h in normalized_allowed
        )
        if not matched:
            raise ValidationError(f"Retailer host '{hostname}' is not approved", field="redirect_url")

    return raw_url


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
        allowed_hosts: set[str] | None = None,
    ) -> None:
        self.commerce_uow = commerce_uow
        self.profile_uow = profile_uow
        self.catalog_uow = catalog_uow
        self.allowed_hosts = allowed_hosts

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

            offer_garment_id = getattr(offer, "garment_id", getattr(offer, "canonical_garment_id", None))
            if offer_garment_id and offer_garment_id != cmd.garment_id:
                raise ValidationError(
                    f"Offer {cmd.offer_id} does not belong to garment {cmd.garment_id}",
                    field="offer_id",
                )

            product = await self.catalog_uow.merchant_products.get_by_source_id(
                offer.merchant_id, offer.source_product_id
            )
            if product is None or not getattr(product, "source_url", None):
                raise ValidationError(
                    "Merchant product has no verified purchase destination URL",
                    field="source_url",
                )

            # Check cleared status if product has an associated catalog source
            if getattr(product, "source_id", None) and hasattr(self.catalog_uow, "sources"):
                src = await self.catalog_uow.sources.get_by_id(product.source_id)
                if src and src.status != "cleared":
                    raise ValidationError(
                        f"Catalog source '{src.name}' is not cleared for commerce handoff",
                        field="source_id",
                    )

            raw_destination_url = product.source_url

        # Validate URL scheme, credentials, and allowed hosts
        validate_retailer_url(raw_destination_url, self.allowed_hosts)

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
