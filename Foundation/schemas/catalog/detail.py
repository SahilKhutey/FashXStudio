from pydantic import BaseModel, ConfigDict

from schemas.catalog.enrichment import GarmentEnrichment
from schemas.catalog.garment import CanonicalGarment, MerchantOffer
from schemas.catalog.garment_image import GarmentImage


class CatalogDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    garment: CanonicalGarment
    images: list[GarmentImage]
    offers: list[MerchantOffer]
    enrichment: GarmentEnrichment | None = None
