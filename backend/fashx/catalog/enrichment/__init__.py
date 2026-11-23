from __future__ import annotations

from .contracts import (
    AttributeResult,
    AttributeSource,
    AttributeStatus,
    EnrichmentEvidence,
    EnrichmentImageAsset,
    EnrichmentInput,
    EnrichmentOutput,
    EnrichmentPermissions,
    EnrichmentStatus,
    EvidenceType,
    ProductContent,
    ReviewFlag,
    ReviewStatus,
    ReviewSummary,
)
from .enricher import HeuristicGarmentEnricher
from .model_gateway import (
    MockTextEnrichmentProvider,
    ModelGateway,
    ModelProviderError,
    ModelRunMetadata,
    TextEnrichmentProvider,
)
from .orchestrator import ENRICHMENT_VERSION, EnrichmentOrchestrator, compute_idempotency_key
from .policy import (
    AI_ALLOWED_INFERENCES,
    FABRIC_EVIDENCE_REQUIRED,
    SOURCE_ONLY_ATTRIBUTES,
    EnrichmentPolicyError,
    validate_fabric_claim,
    validate_model_attributes,
    validate_size_claim,
)
from .ports import EnrichmentResult, GarmentAttributes, GarmentEnricherPort
from .review_service import (
    ReviewAction,
    ReviewEvent,
    ReviewPermissionError,
    ReviewRecord,
    ReviewService,
    ReviewStatusState,
)
from .title_extractor import ExtractedMatch, extract_title_attributes

__all__ = [
    # Contracts
    "AttributeResult",
    "AttributeSource",
    "AttributeStatus",
    "EnrichmentEvidence",
    "EnrichmentImageAsset",
    "EnrichmentInput",
    "EnrichmentOutput",
    "EnrichmentPermissions",
    "EnrichmentStatus",
    "EvidenceType",
    "ProductContent",
    "ReviewFlag",
    "ReviewStatus",
    "ReviewSummary",
    # Legacy / Backwards Compatibility
    "HeuristicGarmentEnricher",
    "GarmentAttributes",
    "EnrichmentResult",
    "GarmentEnricherPort",
    # Policy
    "AI_ALLOWED_INFERENCES",
    "FABRIC_EVIDENCE_REQUIRED",
    "SOURCE_ONLY_ATTRIBUTES",
    "EnrichmentPolicyError",
    "validate_fabric_claim",
    "validate_model_attributes",
    "validate_size_claim",
    # Gateway & Model
    "MockTextEnrichmentProvider",
    "ModelGateway",
    "ModelProviderError",
    "ModelRunMetadata",
    "TextEnrichmentProvider",
    # Orchestrator
    "ENRICHMENT_VERSION",
    "EnrichmentOrchestrator",
    "compute_idempotency_key",
    # Review Service
    "ReviewAction",
    "ReviewEvent",
    "ReviewPermissionError",
    "ReviewRecord",
    "ReviewService",
    "ReviewStatusState",
    # Extraction
    "ExtractedMatch",
    "extract_title_attributes",
]
