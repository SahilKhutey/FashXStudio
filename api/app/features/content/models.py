from collections.abc import Mapping
from dataclasses import dataclass, field

from .enums import ContentStatus, ContentType, ContentVisibility


@dataclass(frozen=True)
class ContentMedia:
    media_id: str
    url: str
    media_type: str
    alt_text: str = ""
    position: int = 0


@dataclass(frozen=True)
class ContentBlock:
    block_id: str
    block_type: str
    data: Mapping[str, object]
    position: int = 0


@dataclass(frozen=True)
class Content:
    content_id: str
    author_id: str
    title: str
    description: str = ""
    content_type: ContentType = ContentType.POST
    status: ContentStatus = ContentStatus.DRAFT
    visibility: ContentVisibility = ContentVisibility.PRIVATE
    media: tuple[ContentMedia, ...] = ()
    blocks: tuple[ContentBlock, ...] = ()
    category: str | None = None
    styles: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    occasions: tuple[str, ...] = ()
    seasons: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    product_ids: tuple[str, ...] = ()
    outfit_ids: tuple[str, ...] = ()
    collection_ids: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)
