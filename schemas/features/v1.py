"""Public, versioned feature-platform contracts.

Feature code uses these contracts to discover capability ownership and to emit
consistent product events without coupling a feature to another feature's
implementation.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from schemas.base import BaseContractModel


class FeatureDomain(StrEnum):
    PLATFORM = "platform"
    USER = "user"
    DISCOVERY = "discovery"
    INTELLIGENCE = "intelligence"
    OUTFIT = "outfit"
    CONTENT = "content"
    SHOPPING = "shopping"
    REGIONAL = "regional"
    ENGAGEMENT = "engagement"


class FeatureStatus(StrEnum):
    PLANNED = "planned"
    DEVELOPMENT = "development"
    BETA = "beta"
    ENABLED = "enabled"
    DISABLED = "disabled"


class FeatureEventType(StrEnum):
    REGISTERED = "feature.registered"
    INITIALIZED = "feature.initialized"
    INITIALIZING = "feature.initializing"
    LOADED = "feature.loaded"
    READY = "feature.ready"
    STARTED = "feature.started"
    ACTION = "feature.action"
    UPDATED = "feature.updated"
    FAILED = "feature.failed"
    RECOVERING = "feature.recovering"
    DISABLED = "feature.disabled"
    COMPLETED = "feature.completed"


class FeatureLifecycle(StrEnum):
    REGISTERED = "registered"
    DISCOVERING_DEPENDENCIES = "discovering_dependencies"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERING = "recovering"
    DISABLED = "disabled"


class FeatureRuntimeState(StrEnum):
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    READY = "ready"
    LOADING = "loading"
    EMPTY = "empty"
    FAILED = "failed"
    RECOVERING = "recovering"
    DISABLED = "disabled"


class FeatureSummary(BaseContractModel):
    id: str = Field(pattern=r"^FX-F(?:0[0-9]|1[0-6])$")
    name: str
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    domain: FeatureDomain
    status: FeatureStatus
    description: str
    depends_on: list[str] = Field(default_factory=list)
    required_core_capabilities: list[str] = Field(default_factory=list)
    routes: list[str] = Field(default_factory=list)
    events: list[FeatureEventType] = Field(default_factory=list)
    default_enabled: bool = True


class FeatureAvailability(BaseContractModel):
    feature: FeatureSummary
    available: bool
    unavailable_reasons: list[str] = Field(default_factory=list)


class FeatureRuntimeSnapshot(BaseContractModel):
    feature_id: str = Field(pattern=r"^FX-F(?:0[0-9]|1[0-6])$")
    lifecycle: FeatureLifecycle
    state: FeatureRuntimeState
    enabled_by_configuration: bool
    available: bool
    unavailable_reasons: list[str] = Field(default_factory=list)


class FeatureEvent(BaseContractModel):
    feature_id: str = Field(pattern=r"^FX-F(?:0[0-9]|1[0-6])$")
    event_type: FeatureEventType
    occurred_at: datetime
    subject_id: str | None = None
    trace_id: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
