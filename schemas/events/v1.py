"""
System Event Telemetry Domain Contracts v1
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import Field
from schemas.base import BaseContractModel


class SystemEventV1(BaseContractModel):
    schema_version: str = Field(default="1.0", frozen=True)
    event_id: str
    user_id: Optional[str] = None
    session_id: str
    event_name: str = Field(
        description="e.g. 'user_registered', 'tryon_started', 'outbound_merchant_clicked'"
    )
    object_type: str = Field(description="e.g. 'garment', 'tryon_job', 'profile'")
    object_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
