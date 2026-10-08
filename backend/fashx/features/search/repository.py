from collections.abc import Iterable

from .models import SearchDocument


class SearchRepository:
    def __init__(self, documents: Iterable[SearchDocument] = ()) -> None:
        self._documents = list(documents)

    def all(self) -> tuple[SearchDocument, ...]:
        return tuple(self._documents)

    def add(self, document: SearchDocument) -> None:
        self._documents.append(document)
