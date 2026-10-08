from collections.abc import Iterable

from .models import Content


class ContentRepository:
    def __init__(self, content: Iterable[Content] = ()) -> None:
        self._content = list(content)

    def add(self, content: Content) -> None:
        self._content.append(content)

    def get(self, content_id: str) -> Content | None:
        return next((c for c in self._content if c.content_id == content_id), None)

    def replace(self, content: Content) -> None:
        self._content[
            self._content.index(
                next(c for c in self._content if c.content_id == content.content_id)
            )
        ] = content
