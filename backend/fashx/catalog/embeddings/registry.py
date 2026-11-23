from __future__ import annotations

import threading
from collections.abc import Callable
from typing import ClassVar

from fashx.catalog.embeddings.base import EmbeddingModelMetadata, ImageEmbeddingAdapter
from fashx.catalog.embeddings.models.mock_adapter import MockViTB32Adapter
from fashx.catalog.embeddings.models.openclip_adapter import OpenCLIPViTB32Adapter


class EmbeddingModelRegistry:
    """Thread-safe registry for approved embedding model adapters."""

    _instance: ClassVar[EmbeddingModelRegistry | None] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self) -> None:
        self._factories: dict[tuple[str, str], Callable[[], ImageEmbeddingAdapter]] = {}
        self._instances: dict[tuple[str, str], ImageEmbeddingAdapter] = {}
        self._metadata_map: dict[tuple[str, str], EmbeddingModelMetadata] = {}
        self._register_default_approved_models()

    @classmethod
    def get_instance(cls) -> EmbeddingModelRegistry:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _register_default_approved_models(self) -> None:
        # 1. Primary baseline: OpenCLIP ViT-B/32
        openclip_meta = EmbeddingModelMetadata(
            model_id="openclip_vit_b32",
            model_version="v1",
            dimension=512,
            architecture="ViT-B/32",
            framework="open_clip",
            description="OpenCLIP ViT-B/32 pretrained on LAION-2B",
        )
        self.register_adapter(
            "openclip_vit_b32",
            "v1",
            openclip_meta,
            lambda: OpenCLIPViTB32Adapter(),
        )

        # 2. Testing mock model
        mock_meta = EmbeddingModelMetadata(
            model_id="mock_vit_b32",
            model_version="v1",
            dimension=512,
            architecture="Mock ViT-B/32",
            framework="deterministic_mock",
            description="Mock deterministic adapter for testing",
        )
        self.register_adapter(
            "mock_vit_b32",
            "v1",
            mock_meta,
            lambda: MockViTB32Adapter(model_id="mock_vit_b32", model_version="v1"),
        )

    def register_adapter(
        self,
        model_id: str,
        model_version: str,
        metadata: EmbeddingModelMetadata,
        factory: Callable[[], ImageEmbeddingAdapter],
    ) -> None:
        key = (model_id, model_version)
        self._metadata_map[key] = metadata
        self._factories[key] = factory
        # Invalidate cached instance if replacing
        if key in self._instances:
            del self._instances[key]

    def get_adapter(
        self, model_id: str = "openclip_vit_b32", model_version: str = "v1"
    ) -> ImageEmbeddingAdapter:
        key = (model_id, model_version)
        if key not in self._factories:
            raise KeyError(
                f"Embedding model '{model_id}:{model_version}' is not approved or registered"
            )
        if key not in self._instances:
            self._instances[key] = self._factories[key]()
        return self._instances[key]

    def get_metadata(
        self, model_id: str, model_version: str = "v1"
    ) -> EmbeddingModelMetadata:
        key = (model_id, model_version)
        if key not in self._metadata_map:
            raise KeyError(f"Metadata for model '{model_id}:{model_version}' not found")
        return self._metadata_map[key]

    def list_approved_models(self) -> list[EmbeddingModelMetadata]:
        return list(self._metadata_map.values())


__all__ = ["EmbeddingModelRegistry"]
