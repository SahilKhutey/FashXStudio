from .models import IntelligenceContext


class IntelligenceContextBuilder:
    def build(self, **kwargs: object) -> IntelligenceContext:
        return IntelligenceContext(**kwargs)
