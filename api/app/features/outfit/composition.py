from dataclasses import replace

from .errors import OutfitItemError
from .models import Outfit, OutfitItem


def add_item(outfit: Outfit, item: OutfitItem) -> Outfit:
    if item.quantity < 1 or any(existing.item_id == item.item_id for existing in outfit.items):
        raise OutfitItemError("Item must be unique and quantity must be at least 1.")
    return replace(outfit, items=(*outfit.items, item))


def remove_item(outfit: Outfit, item_id: str) -> Outfit:
    items = tuple(item for item in outfit.items if item.item_id != item_id)
    if len(items) == len(outfit.items):
        raise OutfitItemError("Item not found.")
    return replace(outfit, items=items)
