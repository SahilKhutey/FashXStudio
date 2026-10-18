from __future__ import annotations

from io import BytesIO
from typing import Any


class MarqoFashionClipEmbedder:
    model_id = "Marqo/marqo-fashionCLIP"
    dim = 512

    def __init__(self) -> None:
        import open_clip  # lazy: only the embedding job needs these
        import torch

        self._torch: Any = torch
        self._model, _, self._pre = open_clip.create_model_and_transforms("hf-hub:Marqo/marqo-fashionCLIP")
        self._tok = open_clip.get_tokenizer("hf-hub:Marqo/marqo-fashionCLIP")
        self._model.eval()

    def embed_images(self, images: list[bytes]) -> list[list[float]]:
        from PIL import Image

        batch = self._torch.stack([self._pre(Image.open(BytesIO(b)).convert("RGB")) for b in images])
        with self._torch.no_grad():
            f = self._model.encode_image(batch)
            f = f / f.norm(dim=-1, keepdim=True)
        return f.tolist()

    def embed_text(self, texts: list[str]) -> list[list[float]]:
        with self._torch.no_grad():
            f = self._model.encode_text(self._tok(texts))
            f = f / f.norm(dim=-1, keepdim=True)
        return f.tolist()
