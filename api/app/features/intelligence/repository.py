from .models import IntelligenceResult


class IntelligenceRepository:
    def __init__(self) -> None:
        self._results: list[IntelligenceResult] = []

    def add(self, result: IntelligenceResult) -> None:
        self._results.append(result)

    def all(self) -> tuple[IntelligenceResult, ...]:
        return tuple(self._results)
