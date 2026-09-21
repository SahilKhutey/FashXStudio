from dataclasses import dataclass


@dataclass(frozen=True)
class CreateOutfitRequest:
    owner_id: str
    name: str
    template_id: str


@dataclass(frozen=True)
class AddOutfitItemRequest:
    outfit_id: str
    product_id: str
    item_type: str
    variant_id: str | None = None


@dataclass(frozen=True)
class UpdateOutfitRequest:
    outfit_id: str
    name: str | None = None
    description: str | None = None
    styles: tuple[str, ...] | None = None
    occasions: tuple[str, ...] | None = None
    seasons: tuple[str, ...] | None = None
    regions: tuple[str, ...] | None = None
