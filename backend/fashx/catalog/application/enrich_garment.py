from dataclasses import dataclass
from uuid import UUID

from database.models.catalog import GarmentEnrichment

from fashx.catalog.enrichment.enricher import HeuristicGarmentEnricher
from fashx.catalog.enrichment.ports import GarmentEnricherPort
from fashx.catalog.repositories.catalog_repository import CatalogUnitOfWork
from api.app.core.errors import EntityNotFoundError


@dataclass
class EnrichGarmentCommand:
    garment_id: UUID
    image_bytes: bytes | None = None


@dataclass
class EnrichGarmentResult:
    enrichment_id: UUID
    garment_id: UUID
    model_version: str
    attributes: dict
    confidence_summary: dict
    garment_version: int


class EnrichGarmentUseCase:
    """Use case orchestrating attribute extraction, confidence scoring, and versioning for a canonical garment."""

    def __init__(
        self,
        uow: CatalogUnitOfWork,
        enricher: GarmentEnricherPort | None = None,
    ) -> None:
        self.uow = uow
        self.enricher = enricher or HeuristicGarmentEnricher()

    async def execute(self, cmd: EnrichGarmentCommand) -> EnrichGarmentResult:
        async with self.uow:
            garment = await self.uow.canonical_garments.get_by_id(cmd.garment_id)
            if garment is None:
                raise EntityNotFoundError("CanonicalGarment", cmd.garment_id)

            # Retrieve context from offers/products linked to this garment
            offers = await self.uow.offers.list_for_garment(cmd.garment_id)
            combined_text = f"{garment.category} {garment.subcategory or ''}"
            for offer in offers:
                product = await self.uow.merchant_products.get_by_source_id(
                    offer.merchant_id, offer.source_product_id
                )
                if product:
                    combined_text += f" {product.title} {product.description or ''}"

            # Run enrichment
            enriched = await self.enricher.enrich(
                title=combined_text,
                description=None,
                image_bytes=cmd.image_bytes,
            )

            attrs_dict = enriched.attributes.to_dict()

            enrichment = GarmentEnrichment(
                garment_id=garment.id,
                model_version=enriched.model_version,
                attributes_json=attrs_dict,
                embedding=enriched.embedding,
                confidence_summary=enriched.confidence_summary,
            )
            self.uow.enrichments.add(enrichment)

            # Update garment version to reflect enrichment evolution
            garment.version += 1
            await self.uow.flush()
            await self.uow.commit()

            return EnrichGarmentResult(
                enrichment_id=enrichment.id,
                garment_id=garment.id,
                model_version=enrichment.model_version,
                attributes=attrs_dict,
                confidence_summary=enriched.confidence_summary,
                garment_version=garment.version,
            )
