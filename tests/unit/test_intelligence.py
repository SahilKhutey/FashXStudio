from api.app.features.intelligence.analyzers import RuleBasedFashionAnalyzer
from api.app.features.intelligence.compatibility import CompatibilityEngine
from api.app.features.intelligence.context import IntelligenceContextBuilder
from api.app.features.intelligence.contracts import IntelligenceRequest
from api.app.features.intelligence.enums import IntelligenceStatus, IntelligenceType
from api.app.features.intelligence.repository import IntelligenceRepository
from api.app.features.intelligence.service import FashionIntelligenceService


def test_rule_analysis_and_compatibility_are_explainable() -> None:
    context = IntelligenceContextBuilder().build(
        styles=("casual",), occasions=("everyday",), seasons=("summer",)
    )
    result = FashionIntelligenceService(
        IntelligenceRepository(), RuleBasedFashionAnalyzer(), IntelligenceContextBuilder()
    ).analyze(IntelligenceRequest("u", "p", IntelligenceType.PRODUCT_ANALYSIS))
    assert result.status == IntelligenceStatus.COMPLETED
    assert len(RuleBasedFashionAnalyzer().analyze("p", context)) == 3
    assert CompatibilityEngine().evaluate(styles_a=("casual",), styles_b=("casual",)).compatible
