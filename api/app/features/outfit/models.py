from collections.abc import Mapping
from dataclasses import dataclass, field

from .enums import OutfitItemType, OutfitStatus, OutfitVisibility


@dataclass(frozen=True)
class OutfitItem:
    item_id: str
    product_id: str
    item_type: OutfitItemType
    variant_id: str | None = None
    position: int = 0
    quantity: int = 1


@dataclass(frozen=True)
class Outfit:
    outfit_id: str
    owner_id: str
    name: str
    description: str = ""
    status: OutfitStatus = OutfitStatus.DRAFT
    visibility: OutfitVisibility = OutfitVisibility.PRIVATE
    items: tuple[OutfitItem, ...] = ()
    styles: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    occasions: tuple[str, ...] = ()
    seasons: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    colors: tuple[str, ...] = ()
    template_id: str | None = None
    related_content_ids: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)
