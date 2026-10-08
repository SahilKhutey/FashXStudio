from .contracts import BasicProfileInput, ContextInput
from .errors import ProfileValidationError


def validate_basic_profile(data: BasicProfileInput) -> None:
    name = data.display_name.strip()
    if not name:
        raise ProfileValidationError("Display name is required.")
    if len(name) > 80:
        raise ProfileValidationError("Display name cannot exceed 80 characters.")


def validate_context(data: ContextInput) -> None:
    if data.region is not None and len(data.region.strip()) > 120:
        raise ProfileValidationError("Region value is too long.")
