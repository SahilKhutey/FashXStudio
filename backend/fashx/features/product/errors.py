class ProductError(Exception):
    pass


class ProductNotFoundError(ProductError):
    pass


class ProductUnavailableError(ProductError):
    pass


class VariantNotFoundError(ProductError):
    pass


class VariantUnavailableError(ProductError):
    pass
