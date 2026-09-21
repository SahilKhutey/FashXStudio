from uuid import uuid4

from .analyzers import FashionAnalyzer
from .context import IntelligenceContextBuilder
from .contracts import IntelligenceRequest
from .enums import IntelligenceStatus
from .errors import IntelligenceValidationError
from .models import IntelligenceResult
from .repository import IntelligenceRepository


class FashionIntelligenceService:
    def __init__(
        self,
        repository: IntelligenceRepository,
        analyzer: FashionAnalyzer,
        context_builder: IntelligenceContextBuilder,
    ) -> None:
        self.repository, self.analyzer, self.context_builder = repository, analyzer, context_builder

    def analyze(self, request: IntelligenceRequest) -> IntelligenceResult:
        if (
            not request.target_id.strip()
            or request.user_id is not None
            and not request.user_id.strip()
        ):
            raise IntelligenceValidationError("A target ID and valid user ID are required.")
        context = self.context_builder.build(user_id=request.user_id, region=request.region)
        attributes = self.analyzer.analyze(request.target_id, context)
        result = IntelligenceResult(
            str(uuid4()),
            str(uuid4()),
            request.intelligence_type,
            IntelligenceStatus.COMPLETED,
            attributes,
            model_version="rules-1.0",
        )
        self.repository.add(result)
        return result
