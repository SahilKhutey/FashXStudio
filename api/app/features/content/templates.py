from dataclasses import dataclass


@dataclass(frozen=True)
class ContentTemplate:
    template_id: str
    name: str
    content_type: str
    required_blocks: tuple[str, ...]
    optional_blocks: tuple[str, ...]


TEMPLATES = {
    "fashion_post": ContentTemplate(
        "fashion_post", "Fashion Post", "post", ("image", "text"), ("product", "outfit", "cta")
    ),
    "lookbook": ContentTemplate(
        "lookbook", "Lookbook", "lookbook", ("hero", "text", "outfit"), ("product", "tip", "cta")
    ),
    "style_guide": ContentTemplate(
        "style_guide",
        "Style Guide",
        "style_guide",
        ("hero", "text", "tip"),
        ("product", "outfit", "collection", "cta"),
    ),
    "product_story": ContentTemplate(
        "product_story",
        "Product Story",
        "product_story",
        ("product", "text"),
        ("image", "outfit", "tip"),
    ),
}


def get_template(template_id: str) -> ContentTemplate | None:
    return TEMPLATES.get(template_id)
