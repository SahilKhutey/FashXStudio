from __future__ import annotations

from dataclasses import dataclass

PRODUCT_NAME = "FashXStudio"
CORE_VERSION = "1.0.0"
CORE_API_VERSION = "v1"
SYSTEM_STAGE = "core"
RELEASE_STATUS = "production-ready"


@dataclass(frozen=True, slots=True)
class BuildInfo:
    product: str
    core_version: str
    api_version: str
    stage: str
    release_status: str


BUILD_INFO = BuildInfo(
    product=PRODUCT_NAME,
    core_version=CORE_VERSION,
    api_version=CORE_API_VERSION,
    stage=SYSTEM_STAGE,
    release_status=RELEASE_STATUS,
)

__all__ = [
    "BUILD_INFO",
    "BuildInfo",
    "CORE_API_VERSION",
    "CORE_VERSION",
    "PRODUCT_NAME",
    "RELEASE_STATUS",
    "SYSTEM_STAGE",
]
