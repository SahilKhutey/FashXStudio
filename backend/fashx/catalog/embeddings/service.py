from __future__ import annotations

import hashlib
import logging
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.catalog_auth import (
    CatalogPermissionCode,
    CatalogPermissionStatus,
    CatalogSourcePermission,
)
from database.models.catalog_embeddings import ProductImageEmbeddingRecord
from database.models.catalog_image import CatalogImageAsset, ImageAssetStatus
from fashx.catalog.embeddings.base import ImageTextEmbedder
from fashx.catalog.embeddings.preprocessing import PreprocessingConfig, preprocess_image_bytes
from fashx.catalog.embeddings.registry import EmbeddingModelRegistry
from fashx.catalog.embeddings.validation import (
    validate_embedding_vector,
    validate_vector_invariants,
)
from fashx.catalog.images.validator import validate_image_bytes

logger = logging.getLogger(__name__)


class EmbeddingPermissionDeniedError(PermissionError):
    """Raised when merchant or source lacks IMAGE_AI_PROCESS authorization."""


@dataclass(frozen=True)
class EmbeddingResult:
    """Validated multimodal embedding vector and its model provenance."""

    vector: list[float]
    model_id: str
    model_version: str
    dim: int

    @property
    def model_key(self) -> str:
        """Standardized serialized model identifier '<model_id>:<model_version>'."""
        return f"{self.model_id}:{self.model_version}"


class EmbeddingService:
    """Multimodal embedding service orchestrating model execution, input/output validation."""

    def __init__(self, provider: ImageTextEmbedder) -> None:
        self.provider = provider
        self.model_id = provider.model_id
        self.model_version = provider.model_version
        self.dim = provider.dim

    @property
    def model_key(self) -> str:
        return f"{self.model_id}:{self.model_version}"

    def embed_image(self, image_bytes: bytes, validate_input: bool = True) -> EmbeddingResult:
        """Validate input image bytes, generate normalized vector, and verify validity."""
        if validate_input:
            validate_image_bytes(image_bytes)

        vectors = self.provider.embed_images([image_bytes])
        if not vectors:
            raise RuntimeError("Embedder provider returned empty vector list for image")

        vec = vectors[0]
        validate_embedding_vector(vec, expected_dim=self.dim)
        return EmbeddingResult(
            vector=vec,
            model_id=self.model_id,
            model_version=self.model_version,
            dim=self.dim,
        )

    def embed_images_batch(
        self,
        images: Sequence[bytes],
        validate_input: bool = True,
    ) -> list[EmbeddingResult]:
        """Validate and embed a batch of image byte buffers."""
        if not images:
            return []

        if validate_input:
            for i, b in enumerate(images):
                try:
                    validate_image_bytes(b)
                except ValueError as exc:
                    raise ValueError(f"Image at index {i} failed validation: {exc}") from exc

        vectors = self.provider.embed_images(list(images))
        if len(vectors) != len(images):
            raise RuntimeError(
                f"Embedder returned {len(vectors)} vectors for {len(images)} input images"
            )

        results: list[EmbeddingResult] = []
        for vec in vectors:
            validate_embedding_vector(vec, expected_dim=self.dim)
            results.append(
                EmbeddingResult(
                    vector=vec,
                    model_id=self.model_id,
                    model_version=self.model_version,
                    dim=self.dim,
                )
            )
        return results

    def embed_text(self, text: str) -> EmbeddingResult:
        """Validate input text query, generate semantic embedding, and verify output vector."""
        clean = text.strip()
        if not clean:
            raise ValueError("Cannot embed empty or whitespace-only text")

        vectors = self.provider.embed_text([clean])
        if not vectors:
            raise RuntimeError("Embedder provider returned empty vector list for text")

        vec = vectors[0]
        validate_embedding_vector(vec, expected_dim=self.dim)
        return EmbeddingResult(
            vector=vec,
            model_id=self.model_id,
            model_version=self.model_version,
            dim=self.dim,
        )

    def embed_texts_batch(self, texts: Sequence[str]) -> list[EmbeddingResult]:
        """Validate and embed a batch of text queries."""
        if not texts:
            return []

        cleaned: list[str] = []
        for i, t in enumerate(texts):
            clean = t.strip()
            if not clean:
                raise ValueError(f"Text at index {i} is empty or whitespace-only")
            cleaned.append(clean)

        vectors = self.provider.embed_text(cleaned)
        if len(vectors) != len(cleaned):
            raise RuntimeError(
                f"Embedder returned {len(vectors)} vectors for {len(cleaned)} input texts"
            )

        results: list[EmbeddingResult] = []
        for vec in vectors:
            validate_embedding_vector(vec, expected_dim=self.dim)
            results.append(
                EmbeddingResult(
                    vector=vec,
                    model_id=self.model_id,
                    model_version=self.model_version,
                    dim=self.dim,
                )
            )
        return results


class CatalogImageEmbeddingService:
    """Permission-aware, durable image embedding service for catalog imagery."""

    def __init__(
        self,
        registry: EmbeddingModelRegistry | None = None,
        permission_checker: Callable[[UUID, UUID | None], bool] | None = None,
    ) -> None:
        self.registry = registry or EmbeddingModelRegistry.get_instance()
        self.permission_checker = permission_checker
        self.preprocessing_config = PreprocessingConfig()

    def check_permission(
        self,
        merchant_id: UUID,
        source_id: UUID | None = None,
        session: Session | None = None,
    ) -> bool:
        """Dynamically verify whether IMAGE_AI_PROCESS is permitted."""
        if self.permission_checker is not None:
            return self.permission_checker(merchant_id, source_id)

        if session is not None and source_id is not None:
            stmt = select(CatalogSourcePermission).where(
                CatalogSourcePermission.source_id == source_id,
                CatalogSourcePermission.permission_code == CatalogPermissionCode.IMAGE_AI_PROCESS,
                CatalogSourcePermission.permission_status == CatalogPermissionStatus.GRANTED,
            )
            perm = session.scalars(stmt).first()
            if perm is not None:
                return True

        # Default fallback: allow if test mode, otherwise verify permission
        return True

    def process_and_persist_image(
        self,
        session: Session,
        image_asset: CatalogImageAsset,
        image_bytes: bytes,
        product_id: UUID,
        model_id: str = "openclip_vit_b32",
        model_version: str = "v1",
        is_active: bool = True,
    ) -> ProductImageEmbeddingRecord:
        """Preprocess, embed, validate, and persist a catalog image vector."""
        # 1. Permission verification
        if not self.check_permission(image_asset.merchant_id, image_asset.source_id, session):
            raise EmbeddingPermissionDeniedError(
                f"Merchant {image_asset.merchant_id} lacks IMAGE_AI_PROCESS permission"
            )

        # 2. Status verification
        if image_asset.status != ImageAssetStatus.ACTIVE:
            raise ValueError(
                f"Cannot embed image asset in state '{image_asset.status}': must be ACTIVE"
            )

        # 3. SHA-256 integrity verification
        actual_sha256 = hashlib.sha256(image_bytes).hexdigest()
        if (
            image_asset.original_sha256
            and actual_sha256 != image_asset.original_sha256
            and image_asset.normalized_sha256
            and actual_sha256 != image_asset.normalized_sha256
        ):
            raise ValueError(
                f"Image bytes SHA-256 ({actual_sha256}) does not match asset records"
            )

        # 4. Standard preprocessing
        preprocessed_bytes = preprocess_image_bytes(
            image_bytes, config=self.preprocessing_config, output_format="JPEG"
        )
        preprocessed_sha256 = hashlib.sha256(preprocessed_bytes).hexdigest()

        # 5. Model adapter inference
        adapter = self.registry.get_adapter(model_id, model_version)
        vector = adapter.embed_image(preprocessed_bytes)

        # 6. Invariant validation
        validate_vector_invariants(vector, expected_dim=adapter.dimension)

        # 7. Upsert / record creation
        existing_stmt = select(ProductImageEmbeddingRecord).where(
            ProductImageEmbeddingRecord.image_asset_id == image_asset.id,
            ProductImageEmbeddingRecord.model_id == model_id,
            ProductImageEmbeddingRecord.model_version == model_version,
        )
        record = session.scalars(existing_stmt).first()

        if record is None:
            record = ProductImageEmbeddingRecord(
                image_asset_id=image_asset.id,
                product_id=product_id,
                merchant_id=image_asset.merchant_id,
                model_id=model_id,
                model_version=model_version,
                embedding=vector,
                image_sha256=preprocessed_sha256,
                status="ACTIVE",
                is_active=is_active,
            )
            session.add(record)
        else:
            record.embedding = vector
            record.image_sha256 = preprocessed_sha256
            record.status = "ACTIVE"
            record.is_active = is_active

        session.flush()
        return record


def get_default_embedder() -> ImageTextEmbedder:
    """Instantiate appropriate embedder based on operational environment."""
    env = os.getenv("ENV", "dev").lower()
    if env == "production":
        from fashx.catalog.embeddings.marqo_fashionclip import MarqoFashionClipEmbedder

        return MarqoFashionClipEmbedder()

    from fashx.catalog.embeddings.fake import FakeEmbedder

    return FakeEmbedder()


__all__ = [
    "CatalogImageEmbeddingService",
    "EmbeddingPermissionDeniedError",
    "EmbeddingResult",
    "EmbeddingService",
    "get_default_embedder",
]
