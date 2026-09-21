from dataclasses import dataclass


@dataclass(frozen=True)
class OutfitTemplate:
    template_id: str
    required_item_types: tuple[str, ...]


TEMPLATES = {
    "everyday": OutfitTemplate("everyday", ("top", "bottom")),
    "dress_based": OutfitTemplate("dress_based", ("dress",)),
    "complete_look": OutfitTemplate("complete_look", ("top", "bottom", "footwear")),
}


def get_template(template_id: str) -> OutfitTemplate | None:
    return TEMPLATES.get(template_id)
