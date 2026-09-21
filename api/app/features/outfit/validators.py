from .errors import OutfitValidationError
from .models import Outfit
from .templates import get_template


def validate_outfit(outfit: Outfit) -> None:
    template = get_template(outfit.template_id or "")
    if not outfit.name.strip() or len(outfit.name) > 120 or template is None:
        raise OutfitValidationError("A valid name and template are required.")
    missing = set(template.required_item_types) - {item.item_type.value for item in outfit.items}
    if missing:
        raise OutfitValidationError(f"Missing required item types: {missing}")
