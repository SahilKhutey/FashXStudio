"""
Pure Domain Value Objects and Entities
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class PhotoCapability:
    photo_id: str
    user_id: str
    job_id: str
    purpose: str
    expires_at: datetime


@dataclass(frozen=True)
class TryOnDecision:
    is_cached: bool
    artifact_key: str
    existing_result_url: Optional[str] = None
