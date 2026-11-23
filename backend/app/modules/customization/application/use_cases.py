import copy
from typing import Any
from uuid import UUID, uuid4

from app.modules.customization.application.services.customization_validator import (
    get_customization_validator,
)
from app.modules.customization.application.services.theme_resolver import (
    get_theme_resolver,
)
from app.modules.customization.domain.entities import CustomizationDraft
from app.modules.customization.domain.exceptions import (
    CustomizationConflictError,
    CustomizationNotFoundError,
    InvalidCustomizationError,
)
from app.modules.customization.infrastructure.persistence.customization_repository import (
    get_customization_repository,
)

DEFAULT_INITIAL_CONFIG = {
    "configuration_version": "1.0.0",
    "schema_version": "1.0.0",
    "theme": {
        "id": "theme-minimal",
        "version": "1.0.0",
        "overrides": {},
    },
    "layout": {
        "id": "layout-grid",
        "version": "1.0.0",
        "settings": {
            "columns": 2,
            "density": "comfortable",
            "image_position": "top",
            "category_navigation_style": "pills",
        },
        "responsive": {},
    },
    "components": [
        {
            "id": "inst-header-1",
            "component_id": "restaurant-header",
            "slot": "header",
            "order": 1,
            "visible": True,
            "props": {
                "show_logo": True,
                "show_cover_photo": True,
                "show_hours": True,
                "show_address": True,
                "alignment": "center",
            },
        },
        {
            "id": "inst-nav-1",
            "component_id": "category-navigation",
            "slot": "navigation",
            "order": 2,
            "visible": True,
            "props": {
                "style": "pills",
                "show_item_counts": False,
                "sticky": True,
            },
        },
        {
            "id": "inst-card-1",
            "component_id": "menu-item-card",
            "slot": "content",
            "order": 3,
            "visible": True,
            "props": {
                "show_image": True,
                "image_aspect_ratio": "4/3",
                "show_description": True,
                "show_allergens": True,
                "show_dietary_badges": True,
                "card_clickable": True,
            },
        },
        {
            "id": "inst-footer-1",
            "component_id": "restaurant-footer",
            "slot": "footer",
            "order": 4,
            "visible": True,
            "props": {
                "show_social_links": True,
                "show_allergen_notice": True,
                "show_powered_by": True,
            },
        },
    ],
}


class GetCustomizationUseCase:
    def __init__(self) -> None:
        self.repository = get_customization_repository()

    def execute(self, organization_id: UUID, menu_id: str) -> CustomizationDraft:
        draft = self.repository.get_customization(organization_id, menu_id)
        if draft is None:
            # Initialize initial default draft for onboarding (VAL-01)
            draft = CustomizationDraft(
                id=uuid4(),
                organization_id=organization_id,
                menu_id=menu_id,
                revision=1,
                configuration=copy.deepcopy(DEFAULT_INITIAL_CONFIG),
                status="draft",
            )
            self.repository.save_customization(draft)
        return draft


class UpdateCustomizationUseCase:
    def __init__(self) -> None:
        self.repository = get_customization_repository()
        self.validator = get_customization_validator()

    def execute(
        self,
        organization_id: UUID,
        menu_id: str,
        configuration: dict[str, Any],
        expected_revision: int | None = None,
        actor_id: str | None = None,
    ) -> CustomizationDraft:
        current = self.repository.get_customization(organization_id, menu_id)
        if current is None:
            val_result = self.validator.validate(configuration)
            if not val_result.is_valid:
                raise InvalidCustomizationError(val_result.errors)
            first_draft = CustomizationDraft(
                id=uuid4(),
                organization_id=organization_id,
                menu_id=menu_id,
                revision=1,
                configuration=val_result.normalized_configuration or configuration,
                status="draft",
                created_by=actor_id,
            )
            return self.repository.save_customization(first_draft)

        if expected_revision is not None and current.revision != expected_revision:
            raise CustomizationConflictError(
                expected_revision=expected_revision,
                actual_revision=current.revision,
            )

        # Validate configuration
        val_result = self.validator.validate(configuration)
        if not val_result.is_valid:
            raise InvalidCustomizationError(val_result.errors)

        updated_draft = current.create_next_revision(
            new_config=val_result.normalized_configuration or configuration,
            actor_id=actor_id,
        )
        saved = self.repository.save_customization(updated_draft)
        return saved


class ResetCustomizationUseCase:
    def __init__(self) -> None:
        self.repository = get_customization_repository()

    def execute(
        self,
        organization_id: UUID,
        menu_id: str,
        reset_tokens: bool = True,
        reset_layout: bool = False,
    ) -> CustomizationDraft:
        current = self.repository.get_customization(organization_id, menu_id)
        if current is None:
            raise CustomizationNotFoundError(menu_id)

        new_config = copy.deepcopy(current.configuration)
        if reset_tokens:
            new_config.setdefault("theme", {})["overrides"] = {}
        if reset_layout:
            new_config.setdefault("layout", {})["settings"] = {
                "columns": 2,
                "density": "comfortable",
            }

        updated = current.create_next_revision(new_config)
        return self.repository.save_customization(updated)


class RestoreRevisionUseCase:
    def __init__(self) -> None:
        self.repository = get_customization_repository()
        self.validator = get_customization_validator()

    def execute(
        self,
        organization_id: UUID,
        menu_id: str,
        revision: int,
        actor_id: str | None = None,
    ) -> CustomizationDraft:
        current = self.repository.get_customization(organization_id, menu_id)
        if current is None:
            raise CustomizationNotFoundError(menu_id)

        target_rev = self.repository.get_revision(organization_id, menu_id, revision)
        if target_rev is None:
            raise CustomizationNotFoundError(f"Revision {revision} for menu {menu_id}")

        # Validate target configuration before restoring
        val_result = self.validator.validate(target_rev.configuration)
        if not val_result.is_valid:
            raise InvalidCustomizationError(val_result.errors)

        restored_draft = current.create_next_revision(
            new_config=target_rev.configuration,
            actor_id=actor_id,
        )
        return self.repository.save_customization(restored_draft)


class PreviewCustomizationUseCase:
    def __init__(self) -> None:
        self.validator = get_customization_validator()
        self.resolver = get_theme_resolver()

    def execute(
        self,
        organization_id: UUID,
        menu_id: str,
        configuration: dict[str, Any],
    ) -> dict[str, Any]:
        val_result = self.validator.validate(configuration)
        if not val_result.is_valid:
            raise InvalidCustomizationError(val_result.errors)

        resolved = self.resolver.resolve(
            configuration=val_result.normalized_configuration or configuration,
            menu_id=menu_id,
            revision=0,
        )
        return resolved
