from dataclasses import replace

from .errors import ContentLinkError
from .models import Content


def _link(content: Content, value: str, field: str) -> Content:
    if not value.strip():
        raise ContentLinkError(f"{field}_id is required")
    values = getattr(content, f"{field}_ids")
    return content if value in values else replace(content, **{f"{field}_ids": (*values, value)})


def link_product(content: Content, product_id: str) -> Content:
    return _link(content, product_id, "product")


def link_outfit(content: Content, outfit_id: str) -> Content:
    return _link(content, outfit_id, "outfit")


def link_collection(content: Content, collection_id: str) -> Content:
    return _link(content, collection_id, "collection")
