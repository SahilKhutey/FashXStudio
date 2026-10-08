import pytest

from fashx.features.outfit.contracts import AddOutfitItemRequest, CreateOutfitRequest
from fashx.features.outfit.errors import OutfitValidationError
from fashx.features.outfit.repository import OutfitRepository
from fashx.features.outfit.service import OutfitService


def test_create_compose_and_validate_everyday_outfit() -> None:
    service = OutfitService(OutfitRepository())
    outfit = service.create(CreateOutfitRequest("u", "Summer", "everyday"))
    outfit = service.add_item(AddOutfitItemRequest(outfit.outfit_id, "top", "top"))
    outfit = service.add_item(AddOutfitItemRequest(outfit.outfit_id, "bottom", "bottom", "m"))
    assert service.validate(outfit.outfit_id).items[1].variant_id == "m"


def test_incomplete_outfit_is_a_valid_draft_but_fails_completion_validation() -> None:
    service = OutfitService(OutfitRepository())
    outfit = service.create(CreateOutfitRequest("u", "Draft", "everyday"))
    with pytest.raises(OutfitValidationError):
        service.validate(outfit.outfit_id)
