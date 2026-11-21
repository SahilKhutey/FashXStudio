from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from fashx.catalog.embeddings.base import EmbeddingModelMetadata, ImageEmbeddingAdapter
from fashx.catalog.embeddings.preprocessing import PreprocessingConfig, preprocess_image
from fashx.catalog.embeddings.validation import validate_vector_invariants

logger = logging.getLogger(__name__)


class OpenCLIPViTB32Adapter(ImageEmbeddingAdapter):
    """Production adapter for OpenCLIP ViT-B/32 (LAION-2B / DataComp-1B).

    Generates 512-dimensional L2-normalized embeddings for fashion product images.
    """

    DEFAULT_MODEL_NAME = "ViT-B-32"
    DEFAULT_PRETRAINED = "laion2b_s34b_b79k"

    def __init__(
        self,
        model_id: str = "openclip_vit_b32",
        model_version: str = "v1",
        dimension: int = 512,
        device: str = "cpu",
    ) -> None:
        self._model_id = model_id
        self._model_version = model_version
        self._dimension = dimension
        self._device = device
        self._metadata = EmbeddingModelMetadata(
            model_id=model_id,
            model_version=model_version,
            dimension=dimension,
            architecture="ViT-B/32",
            framework="open_clip",
            description="OpenCLIP ViT-B/32 pretrained on LAION-2B (512-dim)",
        )
        self._preprocessing_config = PreprocessingConfig()
        self._model: Any = None
        self._preprocess: Any = None
        self._tokenizer: Any = None

    @property
    def metadata(self) -> EmbeddingModelMetadata:
        return self._metadata

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def dimension(self) -> int:
        return self._dimension

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return

        try:
            import open_clip

            model, _, preprocess = open_clip.create_model_and_transforms(
                self.DEFAULT_MODEL_NAME,
                pretrained=self.DEFAULT_PRETRAINED,
                device=self._device,
            )
            model.eval()
            self._model = model
            self._preprocess = preprocess
            self._tokenizer = open_clip.get_tokenizer(self.DEFAULT_MODEL_NAME)
            logger.info("Successfully loaded OpenCLIP ViT-B/32 on device %s", self._device)
        except ImportError:
            logger.warning(
                "open_clip or torch not installed. Running in mock fallback mode for testing."
            )
            from fashx.catalog.embeddings.models.mock_adapter import MockViTB32Adapter

            self._fallback = MockViTB32Adapter(
                model_id=self._model_id,
                model_version=self._model_version,
                dimension=self._dimension,
            )
            self._model = "fallback"

    def embed_image(self, image_bytes: bytes) -> list[float]:
        """Embed single image bytes into an L2-normalized 512-dim vector."""
        self._ensure_loaded()
        if self._model == "fallback":
            return self._fallback.embed_image(image_bytes)

        import torch

        # Standard deterministic preprocessing
        pil_img = preprocess_image(image_bytes, self._preprocessing_config)
        tensor = self._preprocess(pil_img).unsqueeze(0).to(self._device)

        with torch.no_grad():
            features = self._model.encode_image(tensor)
            features = features / features.norm(dim=-1, keepdim=True)
            vec = features.squeeze(0).cpu().tolist()

        validate_vector_invariants(vec, expected_dim=self._dimension)
        return vec

    def embed_batch(self, images: Sequence[bytes]) -> list[list[float]]:
        """Embed a sequence of image bytes into L2-normalized 512-dim vectors."""
        self._ensure_loaded()
        if self._model == "fallback":
            return self._fallback.embed_batch(images)

        if not images:
            return []

        import torch

        tensors = []
        for b in images:
            pil_img = preprocess_image(b, self._preprocessing_config)
            tensors.append(self._preprocess(pil_img))

        batch_tensor = torch.stack(tensors).to(self._device)

        with torch.no_grad():
            features = self._model.encode_image(batch_tensor)
            features = features / features.norm(dim=-1, keepdim=True)
            vectors = features.cpu().tolist()

        for vec in vectors:
            validate_vector_invariants(vec, expected_dim=self._dimension)

        return vectors

    # Multimodal / text compatibility
    def embed_images(self, images: list[bytes]) -> list[list[float]]:
        return self.embed_batch(images)

    def embed_text(self, texts: list[str]) -> list[list[float]]:
        self._ensure_loaded()
        if self._model == "fallback":
            return self._fallback.embed_text(texts)

        if not texts:
            return []

        import torch

        tokens = self._tokenizer(texts).to(self._device)
        with torch.no_grad():
            features = self._model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
            vectors = features.cpu().tolist()

        for vec in vectors:
            validate_vector_invariants(vec, expected_dim=self._dimension)

        return vectors


__all__ = ["OpenCLIPViTB32Adapter"]
