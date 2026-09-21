from dataclasses import replace
from uuid import uuid4

from .composition import add_item
from .contracts import AddOutfitItemRequest, CreateOutfitRequest, UpdateOutfitRequest
from .enums import OutfitItemType
from .errors import OutfitNotFoundError, OutfitTemplateError
from .models import Outfit, OutfitItem
from .repository import OutfitRepository
from .templates import get_template
from .validators import validate_outfit


class OutfitService:
    def __init__(self, repository: OutfitRepository) -> None:
        self.repository = repository

    def create(self, request: CreateOutfitRequest) -> Outfit:
        if (
            not request.owner_id.strip()
            or not request.name.strip()
            or get_template(request.template_id) is None
        ):
            raise OutfitTemplateError(request.template_id)
        outfit = Outfit(
            str(uuid4()), request.owner_id, request.name, template_id=request.template_id
        )
        self.repository.add(outfit)
        return outfit

    def get(self, outfit_id: str) -> Outfit:
        outfit = self.repository.get(outfit_id)
        if outfit is None:
            raise OutfitNotFoundError(outfit_id)
        return outfit

    def add_item(self, request: AddOutfitItemRequest) -> Outfit:
        outfit = self.get(request.outfit_id)
        updated = add_item(
            outfit,
            OutfitItem(
                str(uuid4()),
                request.product_id,
                OutfitItemType(request.item_type),
                request.variant_id,
                len(outfit.items),
            ),
        )
        self.repository.replace(updated)
        return updated

    def update(self, request: UpdateOutfitRequest) -> Outfit:
        outfit = self.get(request.outfit_id)
        updated = replace(
            outfit,
            **{
                name: getattr(request, name)
                if getattr(request, name) is not None
                else getattr(outfit, name)
                for name in ("name", "description", "styles", "occasions", "seasons", "regions")
            },
        )
        self.repository.replace(updated)
        return updated

    def validate(self, outfit_id: str) -> Outfit:
        outfit = self.get(outfit_id)
        validate_outfit(outfit)
        return outfit
