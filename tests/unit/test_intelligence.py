from fashx.features.intelligence.analyzers import RuleBasedFashionAnalyzer
from fashx.features.intelligence.compatibility import CompatibilityEngine
from fashx.features.intelligence.context import IntelligenceContextBuilder
from fashx.features.intelligence.contracts import IntelligenceRequest
from fashx.features.intelligence.enums import IntelligenceStatus, IntelligenceType
from fashx.features.intelligence.repository import IntelligenceRepository
from fashx.features.intelligence.service import FashionIntelligenceService


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
