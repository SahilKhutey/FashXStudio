from __future__ import annotations

from fashx.catalog.embeddings.fake import FakeEmbedder
from fashx.catalog.embeddings.marqo_fashionclip import MarqoFashionClipEmbedder
from fashx.catalog.embeddings.protocol import ImageEmbedder

__all__ = ["FakeEmbedder", "ImageEmbedder", "MarqoFashionClipEmbedder"]
