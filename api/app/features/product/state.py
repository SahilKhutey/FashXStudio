from .enums import ProductState


class ProductExperienceState:
    def __init__(self) -> None:
        self.state, self.error = ProductState.IDLE, None

    def loading(self) -> None:
        self.state, self.error = ProductState.LOADING, None

    def ready(self) -> None:
        self.state, self.error = ProductState.READY, None

    def selecting_variant(self) -> None:
        self.state, self.error = ProductState.VARIANT_SELECTION, None

    def unavailable(self) -> None:
        self.state = ProductState.UNAVAILABLE

    def failure(self, message: str) -> None:
        self.state, self.error = ProductState.ERROR, message
