from abc import ABC, abstractmethod

from .models import FashionAttribute, IntelligenceContext


class FashionAnalyzer(ABC):
    @abstractmethod
    def analyze(
        self, target_id: str, context: IntelligenceContext
    ) -> tuple[FashionAttribute, ...]: ...


class RuleBasedFashionAnalyzer(FashionAnalyzer):
    def analyze(self, target_id: str, context: IntelligenceContext) -> tuple[FashionAttribute, ...]:
        del target_id
        return tuple(
            FashionAttribute(kind, value, 0.7)
            for kind, values in (
                ("style", context.styles),
                ("occasion", context.occasions),
                ("season", context.seasons),
            )
            for value in values
        )
