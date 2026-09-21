from .enums import DiscoveryStatus


class DiscoveryState:
    def __init__(self) -> None:
        self.status = DiscoveryStatus.IDLE
        self.error: str | None = None

    def loading(self) -> None:
        self.status, self.error = DiscoveryStatus.LOADING, None

    def success(self, has_items: bool) -> None:
        self.status = DiscoveryStatus.READY if has_items else DiscoveryStatus.EMPTY
        self.error = None

    def failure(self, message: str) -> None:
        self.status, self.error = DiscoveryStatus.ERROR, message
