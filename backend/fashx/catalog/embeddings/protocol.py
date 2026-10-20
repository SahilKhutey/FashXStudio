from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ImageEmbedder(Protocol):
    model_id: str
    dim: int

    def embed_images(self, images: list[bytes]) -> list[list[float]]:
        ...

    def embed_text(self, texts: list[str]) -> list[list[float]]:
        ...
