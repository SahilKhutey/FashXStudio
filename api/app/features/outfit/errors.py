class OutfitError(Exception):
    pass


class OutfitNotFoundError(OutfitError):
    pass


class OutfitTemplateError(OutfitError):
    pass


class OutfitValidationError(OutfitError):
    pass


class OutfitItemError(OutfitError):
    pass
