"""
Virtual Try-On Domain Contracts v1
"""

import hashlib
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import Field
from schemas.base import BaseContractModel


class TryOnJobStatus(str, Enum):
    QUEUED = "queued"
    PREPROCESSING = "preprocessing"
    DIFFUSION_INFERENCE = "diffusion_inference"
    POSTPROCESSING_QC = "postprocessing_qc"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TryOnCacheKeyV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    user_photo_version_hash: str
    canonical_garment_version: int
    model_adapter_id: str
    model_weights_version: str
    preprocessing_version: str
    render_config_hash: str

    def compute_sha256(self) -> str:
        payload = (
            f"{self.user_photo_version_hash}:"
            f"{self.canonical_garment_version}:"
            f"{self.model_adapter_id}:"
            f"{self.model_weights_version}:"
            f"{self.preprocessing_version}:"
            f"{self.render_config_hash}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class TryOnJobV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    job_id: str
    user_id: str
    canonical_garment_id: str
    variant_id: Optional[str] = None
    user_photo_id: str
    status: TryOnJobStatus = TryOnJobStatus.QUEUED
    cache_key: str
    result_image_url: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    queue_wait_ms: Optional[int] = None
    inference_duration_ms: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class TryOnStatusResponseV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    job_id: str
    status: TryOnJobStatus
    cache_hit: bool = False
    result_image_url: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    execution_metrics: Dict[str, Any] = Field(default_factory=dict)
    completed_at: Optional[datetime] = None
