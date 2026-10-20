from fastapi import APIRouter
from pydantic import BaseModel

from fashx.core.settings import get_settings

router = APIRouter(tags=["Config"])


class LegalConfig(BaseModel):
    privacy_url: str | None = None
    terms_url: str | None = None


class FlagsConfig(BaseModel):
    tryon: bool


class ConfigResponse(BaseModel):
    min_app_version: str
    maintenance: bool
    tryon_supported_categories: list[str]
    consent_version: str
    legal: LegalConfig
    flags: FlagsConfig


@router.get("/config", response_model=ConfigResponse)
def config() -> ConfigResponse:
    s = get_settings()
    return ConfigResponse(
        min_app_version=s.min_app_version,
        maintenance=s.maintenance_mode,
        tryon_supported_categories=s.tryon_supported_categories,
        consent_version=s.consent_version,
        legal=LegalConfig(
            privacy_url=s.privacy_url,
            terms_url=s.terms_url,
        ),
        flags=FlagsConfig(
            tryon=s.tryon_enabled,
        ),
    )
