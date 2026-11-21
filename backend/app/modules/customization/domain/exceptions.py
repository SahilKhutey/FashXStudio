from typing import Any


class CustomizationDomainError(Exception):
    """Base exception for customization domain errors."""


class CustomizationNotFoundError(CustomizationDomainError):
    def __init__(self, menu_id: str):
        super().__init__(f"Menu customization for menu '{menu_id}' not found")
        self.menu_id = menu_id


class CustomizationConflictError(CustomizationDomainError):
    def __init__(self, expected_revision: int, actual_revision: int):
        super().__init__(
            f"Customization revision conflict: expected revision '{expected_revision}', "
            f"but current revision is '{actual_revision}'"
        )
        self.expected_revision = expected_revision
        self.actual_revision = actual_revision


class TenantAccessDeniedError(CustomizationDomainError):
    def __init__(self, actor_org_id: str, target_org_id: str):
        super().__init__(
            f"Tenant isolation access denied: actor org '{actor_org_id}' cannot access "
            f"resources belonging to org '{target_org_id}'"
        )
        self.actor_org_id = actor_org_id
        self.target_org_id = target_org_id


class PlatformPermissionDeniedError(CustomizationDomainError):
    def __init__(self, action: str):
        super().__init__(f"Platform permission denied for action: {action}")
        self.action = action


class InvalidCustomizationError(CustomizationDomainError):
    def __init__(self, errors: list[Any]):
        super().__init__(f"Customization failed validation with {len(errors)} error(s)")
        self.errors = errors
