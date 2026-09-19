from uuid import UUID

from pydantic import BaseModel, ConfigDict

from schemas.catalog.garment import CanonicalGarment, MerchantOffer
from schemas.catalog.garment_image import GarmentImage


class CatalogDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    garment: CanonicalGarment
    images: list[GarmentImage]
    offers: list[MerchantOffer]
