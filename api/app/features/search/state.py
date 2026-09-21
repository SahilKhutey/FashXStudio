from .enums import SearchStatus


class SearchState:
    def __init__(self) -> None:
        self.status, self.error, self.query = SearchStatus.IDLE, None, ""

    def suggesting(self, query: str) -> None:
        self.status, self.query, self.error = SearchStatus.SUGGESTING, query, None

    def searching(self, query: str) -> None:
        self.status, self.query, self.error = SearchStatus.SEARCHING, query, None

    def success(self, has_results: bool) -> None:
        self.status, self.error = (SearchStatus.READY if has_results else SearchStatus.EMPTY), None

    def failure(self, message: str) -> None:
        self.status, self.error = SearchStatus.ERROR, message
