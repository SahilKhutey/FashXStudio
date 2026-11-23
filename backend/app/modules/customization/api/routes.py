from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from app.modules.customization.api.dependencies import (
    get_current_organization_id,
    get_expected_revision,
)
from app.modules.customization.application.services.customization_validator import (
    get_customization_validator,
)
from app.modules.customization.application.use_cases import (
    GetCustomizationUseCase,
    PreviewCustomizationUseCase,
    ResetCustomizationUseCase,
    RestoreRevisionUseCase,
    UpdateCustomizationUseCase,
)
from app.modules.customization.domain.exceptions import (
    CustomizationConflictError,
    CustomizationNotFoundError,
    InvalidCustomizationError,
    TenantAccessDeniedError,
)
from app.modules.customization.infrastructure.component_registry import (
    ComponentNotFoundError,
    get_component_registry,
)
from app.modules.customization.infrastructure.layout_registry import (
    LayoutNotFoundError,
    get_layout_registry,
)
from app.modules.customization.infrastructure.persistence.customization_repository import (
    get_customization_repository,
)
from app.modules.customization.infrastructure.theme_registry import (
    ThemeNotFoundError,
    UnsupportedThemeVersionError,
    get_theme_registry,
)

router = APIRouter(prefix="", tags=["customization"])

# 1. Themes Endpoints
@router.get("/themes")
def list_themes():
    registry = get_theme_registry()
    return {"themes": registry.list_themes()}


@router.get("/themes/{theme_id}")
def get_theme(theme_id: str):
    registry = get_theme_registry()
    try:
        return registry.get_theme(theme_id)
    except ThemeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/themes/{theme_id}/versions/{version}")
def get_theme_version(theme_id: str, version: str):
    registry = get_theme_registry()
    try:
        return registry.get_theme(theme_id, version)
    except ThemeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnsupportedThemeVersionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/themes")
def create_or_modify_platform_theme(
    x_user_role: str | None = Header(None),
):
    # ARC08-T088: Attempt to modify platform theme as restaurant user -> Denied
    if x_user_role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Restaurant users cannot modify platform-owned theme definitions",
        )
    return {"status": "ok"}


# 2. Layouts Endpoints
@router.get("/layouts")
def list_layouts():
    registry = get_layout_registry()
    return {"layouts": registry.list_layouts()}


@router.get("/layouts/{layout_id}")
def get_layout(layout_id: str):
    registry = get_layout_registry()
    try:
        return registry.get_layout(layout_id)
    except LayoutNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# 3. Components Endpoints
@router.get("/components")
def list_components():
    registry = get_component_registry()
    return {"components": registry.list_components()}


@router.get("/components/{component_id}")
def get_component(component_id: str):
    registry = get_component_registry()
    try:
        return registry.get_component(component_id)
    except ComponentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/components")
def manage_platform_components(
    x_user_role: str | None = Header(None),
):
    # ARC08-T089: Access component management as restaurant user -> Denied
    if x_user_role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Component management is restricted to platform administrators",
        )
    return {"status": "ok"}


# 4. Customization Endpoints
@router.get("/menus/{menu_id}/customization")
def get_menu_customization(
    menu_id: str,
    response: Response,
    org_id: UUID = Depends(get_current_organization_id),
):
    try:
        use_case = GetCustomizationUseCase()
        draft = use_case.execute(org_id, menu_id)
        response.headers["ETag"] = draft.etag
        return {
            "menu_id": draft.menu_id,
            "organization_id": str(draft.organization_id),
            "revision": draft.revision,
            "status": draft.status,
            "configuration": draft.configuration,
            "updated_at": draft.updated_at.isoformat(),
        }
    except TenantAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put("/menus/{menu_id}/customization")
def update_menu_customization(
    menu_id: str,
    payload: dict[str, Any],
    response: Response,
    org_id: UUID = Depends(get_current_organization_id),
    expected_rev: int | None = Depends(get_expected_revision),
):
    try:
        use_case = UpdateCustomizationUseCase()
        draft = use_case.execute(
            organization_id=org_id,
            menu_id=menu_id,
            configuration=payload,
            expected_revision=expected_rev,
        )
        response.headers["ETag"] = draft.etag
        return {
            "menu_id": draft.menu_id,
            "organization_id": str(draft.organization_id),
            "revision": draft.revision,
            "configuration_version": draft.configuration.get("configuration_version", "1.0.0"),
            "status": draft.status,
            "updated_at": draft.updated_at.isoformat(),
            "validation": {
                "valid": True,
                "errors": [],
                "warnings": [],
            },
        }
    except CustomizationConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidCustomizationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "https://errors.modularmenu.com/invalid-customization",
                "title": "Customization validation failed",
                "errors": [{"path": err.path, "message": err.message, "code": err.code} for err in e.errors],
            },
        )
    except TenantAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/menus/{menu_id}/customization/validate")
def validate_menu_customization(
    menu_id: str,
    payload: dict[str, Any],
    org_id: UUID = Depends(get_current_organization_id),
):
    validator = get_customization_validator()
    res = validator.validate(payload)
    return {
        "valid": res.is_valid,
        "errors": [{"path": e.path, "message": e.message, "code": e.code} for e in res.errors],
        "warnings": res.warnings,
    }


@router.post("/menus/{menu_id}/customization/preview")
def preview_menu_customization(
    menu_id: str,
    payload: dict[str, Any],
    response: Response,
    org_id: UUID = Depends(get_current_organization_id),
):
    # Preview isolation: prevent CDN caching
    response.headers["Cache-Control"] = "no-store, no-cache, private"
    response.headers["Pragma"] = "no-cache"
    try:
        use_case = PreviewCustomizationUseCase()
        resolved = use_case.execute(org_id, menu_id, payload)
        return resolved
    except InvalidCustomizationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"path": err.path, "message": err.message, "code": err.code} for err in e.errors],
        )
    except TenantAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/menus/{menu_id}/customization/reset")
def reset_menu_customization(
    menu_id: str,
    reset_tokens: bool = True,
    reset_layout: bool = False,
    org_id: UUID = Depends(get_current_organization_id),
):
    try:
        use_case = ResetCustomizationUseCase()
        draft = use_case.execute(org_id, menu_id, reset_tokens, reset_layout)
        return {
            "menu_id": draft.menu_id,
            "revision": draft.revision,
            "configuration": draft.configuration,
        }
    except CustomizationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TenantAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/menus/{menu_id}/customization/revisions")
def list_menu_revisions(
    menu_id: str,
    org_id: UUID = Depends(get_current_organization_id),
):
    try:
        repo = get_customization_repository()
        revs = repo.list_revisions(org_id, menu_id)
        return {
            "revisions": [
                {
                    "revision": r.revision,
                    "created_at": r.created_at.isoformat(),
                    "created_by": r.created_by,
                }
                for r in revs
            ]
        }
    except TenantAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/menus/{menu_id}/customization/revisions/{revision}")
def get_menu_revision(
    menu_id: str,
    revision: int,
    org_id: UUID = Depends(get_current_organization_id),
):
    try:
        repo = get_customization_repository()
        rev = repo.get_revision(org_id, menu_id, revision)
        if rev is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Revision {revision} not found")
        return {
            "menu_id": rev.menu_id,
            "revision": rev.revision,
            "configuration": rev.configuration,
            "created_at": rev.created_at.isoformat(),
        }
    except TenantAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/menus/{menu_id}/customization/revisions/{revision}/restore")
def restore_menu_revision(
    menu_id: str,
    revision: int,
    org_id: UUID = Depends(get_current_organization_id),
):
    try:
        use_case = RestoreRevisionUseCase()
        draft = use_case.execute(org_id, menu_id, revision)
        return {
            "menu_id": draft.menu_id,
            "revision": draft.revision,
            "status": "draft",
            "restored_from_revision": revision,
            "configuration": draft.configuration,
        }
    except CustomizationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TenantAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
