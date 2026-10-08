"""Unit tests for AI / Intelligence Screens & Interaction System — Phase 12.

Verifies:
- AI-001 to AI-005: AI Home (AI01), hero capabilities, suggested tasks, sessions
- AI-010 to AI-017: Multi-turn Conversation & Session (AI02), citations, explicit actions
- AI-020 to AI-023: Context Items & Active Context Management
- AI-030 to AI-036: Explainable Recommendations, Qualitative Confidence & Feedback (AI07, AI08)
- AI-040 to AI-046: AI Search & Intent Extraction with Observable Steps (AI06)
- AI-050 to AI-055: Product Assistant & Fact vs Guidance Boundary (AI03)
- AI-060 to AI-066: Style & Outfit Assistant with User Edit Controls (AI04, AI05, AI09)
- FORBID-001 to FORBID-008: Strict extra="forbid" rejection across all AI contracts (Constitution Rule I02).
"""

import pytest
from pydantic import ValidationError

from schemas.visual.ai import (
    AIActionContract,
    AIAssistantTemplateSpecContract,
    AICitationContract,
    AIConfidenceLevel,
    AIContentType,
    AIContextItemContract,
    AIExplanationContract,
    AIFeedbackContract,
    AIFeedbackReason,
    AIFeedbackType,
    AIHomeTemplateSpecContract,
    AIMessageContract,
    AIMessageRole,
    AIMessageState,
    AIOutfitRecommendationTemplateSpecContract,
    AIPreferencesContract,
    AIPreferencesTemplateSpecContract,
    AIProcessingStepContract,
    AIProcessingStepState,
    AIProductAssistantTemplateSpecContract,
    AIRecommendationContract,
    AIRecommendationDetailTemplateSpecContract,
    AIRecommendationFactorContract,
    AIResultExplanationTemplateSpecContract,
    AIScreenId,
    AISearchTemplateSpecContract,
    AISessionContract,
    AIStyleAssistantTemplateSpecContract,
    PostAIFeedbackRequestContract,
    PostAIMessageRequestContract,
)
from fashx.visual.ai_service import (
    CURRENT_PREFERENCES,
    DEFAULT_PREFERENCES,
    FEEDBACK_REGISTRY,
    INITIAL_EXPLANATION,
    INITIAL_RECOMMENDATIONS,
    INITIAL_SESSIONS,
    SESSIONS_REGISTRY,
    ai_search,
    create_ai_session,
    get_ai_assistant_template,
    get_ai_home_template,
    get_ai_preferences,
    get_ai_session,
    get_outfit_recommendation_template,
    get_product_assistant_template,
    get_recommendation_detail,
    get_result_explanation,
    get_style_assistant_template,
    post_ai_message,
    reset_ai_fixtures,
    submit_ai_feedback,
    update_ai_preferences,
)


@pytest.fixture(autouse=True)
def setup_ai_isolation():
    """Ensure in-memory AI session, feedback, and preference registry is fresh."""
    reset_ai_fixtures()
    yield
    reset_ai_fixtures()


# ===========================================================================
# AI-001 to AI-005: AI Home (AI01)
# ===========================================================================

def test_ai_001_home_template_renders():
    """AI-001: get_ai_home_template returns valid AI01 spec with non-empty modules."""
    spec = get_ai_home_template()
    assert spec.screen_id == AIScreenId.AI01_AI_HOME
    assert "Fashion Assistant" in spec.hero_title
    assert "Discover fashion" in spec.hero_subtitle
    assert len(spec.suggested_tasks) == 4
    assert len(spec.quick_prompts) >= 3
    assert len(spec.curated_recommendations) >= 1


def test_ai_002_quick_prompts_present():
    """AI-002: AI Home provides accessible natural-language quick prompts."""
    spec = get_ai_home_template()
    assert any("summer" in p.lower() for p in spec.quick_prompts)
    assert any("selvedge" in p.lower() or "denim" in p.lower() for p in spec.quick_prompts)


def test_ai_003_suggested_tasks_explicit():
    """AI-003: Suggested tasks map to explicit supported tools."""
    spec = get_ai_home_template()
    action_targets = [t.target_id for t in spec.suggested_tasks]
    assert "AI03" in action_targets
    assert "AI04" in action_targets
    assert "AI05" in action_targets
    assert "AI06" in action_targets


def test_ai_004_recent_sessions_populated():
    """AI-004: Recent sessions module includes active conversation history."""
    spec = get_ai_home_template()
    assert len(spec.recent_sessions) >= 1
    assert spec.recent_sessions[0].id == "session-summer-trip"


def test_ai_005_curated_recommendations_confidence():
    """AI-005: Home recommendations display transparent qualitative confidence."""
    spec = get_ai_home_template()
    rec = spec.curated_recommendations[0]
    assert rec.confidence == AIConfidenceLevel.STRONG
    assert rec.explanation.primary_reason is not None


# ===========================================================================
# AI-010 to AI-017: Multi-turn Conversation & Session (AI02)
# ===========================================================================

def test_ai_010_create_session():
    """AI-010: create_ai_session instantiates valid session with default context."""
    sess = create_ai_session(title="Capsule Building")
    assert sess.id.startswith("session-")
    assert sess.title == "Capsule Building"
    assert len(sess.context_items) >= 2
    assert sess.state == AIMessageState.COMPLETE
    assert sess.id in SESSIONS_REGISTRY


def test_ai_011_post_message_and_receive_assistant_reply():
    """AI-011: post_ai_message appends user message and produces assistant response."""
    sess = create_ai_session("Test Query")
    reply = post_ai_message(sess.id, "Find black trousers for evening wear")

    assert reply.role == AIMessageRole.ASSISTANT
    assert "black trousers" in reply.content or "verified" in reply.content
    assert len(reply.citations) >= 1
    assert len(reply.suggested_actions) >= 1
    assert len(sess.messages) == 2
    assert sess.messages[0].role == AIMessageRole.USER
    assert sess.messages[1].role == AIMessageRole.ASSISTANT


def test_ai_012_message_contract_validation():
    """AI-012: AIMessageContract enforces required attributes and defaults."""
    msg = AIMessageContract(
        id="m-123",
        role=AIMessageRole.USER,
        content="Test content",
        created_at="2026-10-02T10:00:00Z",
    )
    assert msg.state == AIMessageState.COMPLETE
    assert msg.context_items == []


def test_ai_013_assistant_template_spec():
    """AI-013: get_ai_assistant_template returns AI02 spec with active context and prompts."""
    spec = get_ai_assistant_template("session-summer-trip")
    assert spec.screen_id == AIScreenId.AI02_AI_FASHION_ASSISTANT
    assert spec.session.id == "session-summer-trip"
    assert len(spec.suggested_prompts) >= 2


def test_ai_014_session_chronological_ordering():
    """AI-014: Session messages preserve strict chronological sequence."""
    sess = SESSIONS_REGISTRY["session-summer-trip"]
    timestamps = [m.created_at for m in sess.messages]
    assert timestamps == sorted(timestamps)


def test_ai_015_citations_backing():
    """AI-015: Assistant citations contain source_id, source_type, and title."""
    sess = SESSIONS_REGISTRY["session-summer-trip"]
    assistant_msg = sess.messages[1]
    assert assistant_msg.citations is not None
    assert len(assistant_msg.citations) >= 1
    cite = assistant_msg.citations[0]
    assert cite.source_id == "cat-textiles"
    assert cite.source_type == "fabric_guide"


def test_ai_016_suggested_actions_structure():
    """AI-016: Suggested actions provide explicit target_id and action_type."""
    sess = SESSIONS_REGISTRY["session-summer-trip"]
    assistant_msg = sess.messages[1]
    assert assistant_msg.suggested_actions is not None
    assert len(assistant_msg.suggested_actions) >= 1
    act = assistant_msg.suggested_actions[0]
    assert act.action_type == "navigate"
    assert act.target_id == "look-mumbai-01"


def test_ai_017_session_not_found_fallback():
    """AI-017: get_ai_session falls back gracefully to default session if not found."""
    sess = get_ai_session("nonexistent-session")
    assert sess.id == "session-summer-trip"


# ===========================================================================
# AI-020 to AI-023: Context System
# ===========================================================================

def test_ai_020_context_item_structure():
    """AI-020: AIContextItemContract carries key, label, value, and removable flag."""
    item = AIContextItemContract(
        key="fabric",
        label="Preferred Fabric",
        value="Linen",
        is_removable=True,
    )
    assert item.key == "fabric"
    assert item.is_removable is True


def test_ai_021_session_carries_context_chips():
    """AI-021: Sessions carry contextual parameters available to AI."""
    sess = SESSIONS_REGISTRY["session-summer-trip"]
    assert len(sess.context_items) == 2
    keys = {c.key for c in sess.context_items}
    assert "destination" in keys
    assert "season" in keys


def test_ai_022_context_items_in_message():
    """AI-022: Messages retain snapshot of active context at transmission time."""
    sess = SESSIONS_REGISTRY["session-summer-trip"]
    user_msg = sess.messages[0]
    assert user_msg.context_items is not None
    assert len(user_msg.context_items) == 2


def test_ai_023_explanation_lists_context_used():
    """AI-023: Explanations explicitly list all context factors used."""
    assert len(INITIAL_EXPLANATION.context_used) >= 3
    assert any("Mumbai" in c for c in INITIAL_EXPLANATION.context_used)


# ===========================================================================
# AI-030 to AI-036: Recommendations, Explanations & Feedback (AI07, AI08)
# ===========================================================================

def test_ai_030_recommendation_contract():
    """AI-030: AIRecommendationContract ties content object to explanation."""
    rec = INITIAL_RECOMMENDATIONS[0]
    assert rec.recommendation_type == "outfit_look"
    assert rec.content_object is not None
    assert rec.explanation.result_id == rec.id


def test_ai_031_explanation_factors_verified():
    """AI-031: AIRecommendationFactorContract has is_verified=True."""
    factors = INITIAL_EXPLANATION.matching_factors
    assert len(factors) >= 3
    assert all(f.is_verified for f in factors)
    assert factors[0].factor_name == "Style Direction"


def test_ai_032_recommendation_detail_spec():
    """AI-032: get_recommendation_detail returns AI07 spec with supporting items and alternatives."""
    spec = get_recommendation_detail("rec-summer-streetwear-01")
    assert spec.screen_id == AIScreenId.AI07_AI_RECOMMENDATION_DETAIL
    assert spec.recommendation.id == "rec-summer-streetwear-01"
    assert len(spec.supporting_products) >= 1
    assert len(spec.alternatives) >= 1


def test_ai_033_result_explanation_spec():
    """AI-033: get_result_explanation returns AI08 spec with contributing factors."""
    spec = get_result_explanation("rec-summer-streetwear-01")
    assert spec.screen_id == AIScreenId.AI08_AI_RESULT_EXPLANATION
    assert spec.result_id == "rec-summer-streetwear-01"
    assert spec.target_item is not None
    assert len(spec.contributing_factors) >= 3


def test_ai_034_qualitative_confidence_enum():
    """AI-034: Confidence uses qualitative labels instead of ungrounded decimals."""
    assert AIConfidenceLevel.STRONG == "strong"
    assert AIConfidenceLevel.POSSIBLE == "possible"
    assert AIConfidenceLevel.LIMITED == "limited"


def test_ai_035_submit_feedback_helpful():
    """AI-035: submit_ai_feedback stores positive evaluation."""
    fb = submit_ai_feedback(
        result_id="rec-summer-streetwear-01",
        feedback_type=AIFeedbackType.HELPFUL,
    )
    assert fb.result_id == "rec-summer-streetwear-01"
    assert fb.feedback_type == AIFeedbackType.HELPFUL
    assert fb.reason is None
    assert len(FEEDBACK_REGISTRY) == 1


def test_ai_036_submit_feedback_not_helpful_with_reason():
    """AI-036: submit_ai_feedback stores negative evaluation with structured reason."""
    fb = submit_ai_feedback(
        result_id="rec-summer-streetwear-01",
        feedback_type=AIFeedbackType.NOT_HELPFUL,
        reason=AIFeedbackReason.TOO_EXPENSIVE,
        note="Looking for items under ₹2,000",
    )
    assert fb.feedback_type == AIFeedbackType.NOT_HELPFUL
    assert fb.reason == AIFeedbackReason.TOO_EXPENSIVE
    assert fb.note == "Looking for items under ₹2,000"


# ===========================================================================
# AI-040 to AI-046: AI Search (AI06)
# ===========================================================================

def test_ai_040_ai_search_style_extraction():
    """AI-040: ai_search extracts style intent from query."""
    spec = ai_search("Find relaxed casual streetwear outfits")
    assert spec.screen_id == AIScreenId.AI06_AI_SEARCH
    assert spec.interpreted_style == "Streetwear"


def test_ai_041_ai_search_context_and_budget_extraction():
    """AI-041: ai_search extracts context and budget constraints."""
    spec = ai_search("Find summer jackets under 3000")
    assert spec.interpreted_context == "Summer"
    assert spec.interpreted_budget == "Under ₹3,000"


def test_ai_042_ai_search_observable_processing_steps():
    """AI-042: ai_search returns multi-stage observable intelligence steps."""
    spec = ai_search("denim")
    assert len(spec.processing_steps) == 3
    assert all(s.state == AIProcessingStepState.COMPLETED for s in spec.processing_steps)
    assert "query" in spec.processing_steps[0].label.lower()


def test_ai_043_ai_search_results_populated():
    """AI-043: ai_search returns verified catalog pieces."""
    spec = ai_search("denim")
    assert spec.total_results >= 1
    assert any("denim" in p.title.lower() for p in spec.results)


def test_ai_044_ai_search_empty_query_fallback():
    """AI-044: ai_search handles empty string gracefully with default items."""
    spec = ai_search("")
    assert spec.total_results >= 1
    assert len(spec.results) >= 1


# ===========================================================================
# AI-050 to AI-055: Product Assistant & Fact vs Guidance Boundary (AI03)
# ===========================================================================

def test_ai_050_product_assistant_spec():
    """AI-050: get_product_assistant_template returns AI03 specification."""
    spec = get_product_assistant_template("prod-denim-01")
    assert spec.screen_id == AIScreenId.AI03_AI_PRODUCT_ASSISTANT
    assert spec.product.id == "prod-denim-01"


def test_ai_051_product_fact_boundary_strict():
    """AI-051: Authoritative catalog facts are never fabricated or replaced by AI."""
    spec = get_product_assistant_template("prod-denim-01")
    assert "Price" in spec.product_facts
    assert "₹4,999.00" in spec.product_facts["Price"]
    assert "In Stock" in spec.product_facts["Availability"]
    assert "Japanese Selvedge" in spec.product_facts["Material"]


def test_ai_052_ai_guidance_labeled_as_recommendation():
    """AI-052: AI styling guidance is clearly differentiated from physical product facts."""
    spec = get_product_assistant_template("prod-denim-01")
    assert len(spec.ai_guidance) > 20
    assert "recommend" in spec.ai_guidance.lower() or "silhouette" in spec.ai_guidance.lower()


def test_ai_053_frequently_asked_and_styling():
    """AI-053: Product assistant includes frequently asked prompts and styling looks."""
    spec = get_product_assistant_template("prod-denim-01")
    assert len(spec.frequently_asked) >= 2
    assert len(spec.styling_suggestions) >= 1
    assert len(spec.similar_products) >= 1


# ===========================================================================
# AI-060 to AI-066: Style & Outfit Assistant (AI04, AI05, AI09)
# ===========================================================================

def test_ai_060_style_assistant_spec():
    """AI-060: get_style_assistant_template returns AI04 spec with matching looks."""
    spec = get_style_assistant_template("style-streetwear")
    assert spec.screen_id == AIScreenId.AI04_AI_STYLE_ASSISTANT
    assert spec.recommended_style.id == "style-streetwear"
    assert len(spec.matching_looks) >= 1
    assert len(spec.suggested_products) >= 1


def test_ai_061_outfit_recommendation_user_control():
    """AI-061: Outfit recommendation has can_edit=True ensuring user remains in control."""
    spec = get_outfit_recommendation_template("look-mumbai-01")
    assert spec.screen_id == AIScreenId.AI05_AI_OUTFIT_RECOMMENDATION
    assert spec.can_edit is True
    assert len(spec.constituent_items) >= 2
    assert len(spec.alternatives) >= 1


def test_ai_062_preferences_retrieval_and_update():
    """AI-062: get_ai_preferences and update_ai_preferences manage AI tuning boundaries."""
    spec = get_ai_preferences("user-default")
    assert spec.screen_id == AIScreenId.AI09_AI_PREFERENCES
    assert spec.preferences.user_id == "user-default"
    assert "Streetwear" in spec.preferences.preferred_styles

    updated_prefs = spec.preferences.model_copy(deep=True)
    updated_prefs.budget_tier = "luxury"
    updated_prefs.preferred_styles = ["Minimalist", "Quiet Luxury"]
    res = update_ai_preferences(updated_prefs)

    assert res.budget_tier == "luxury"
    assert "Quiet Luxury" in res.preferred_styles
    # Verify retrieved template reflects update
    new_spec = get_ai_preferences("user-default")
    assert new_spec.preferences.budget_tier == "luxury"


# ===========================================================================
# FORBID-001 to FORBID-008: Extra Fields Forbidden (Constitution Rule I02)
# ===========================================================================

def test_forbid_001_context_item_extra_field():
    """FORBID-001: AIContextItemContract rejects unauthorized fields."""
    with pytest.raises(ValidationError):
        AIContextItemContract(
            key="k",
            label="L",
            value="V",
            rogue_field="illegal",
        )


def test_forbid_002_citation_extra_field():
    """FORBID-002: AICitationContract rejects unauthorized fields."""
    with pytest.raises(ValidationError):
        AICitationContract(
            source_id="s1",
            source_type="doc",
            title="T",
            extra_hacked=True,
        )


def test_forbid_003_message_extra_field():
    """FORBID-003: AIMessageContract rejects unauthorized fields."""
    with pytest.raises(ValidationError):
        AIMessageContract(
            id="m1",
            role=AIMessageRole.USER,
            content="Hello",
            created_at="now",
            unauthorized_key=123,
        )


def test_forbid_004_explanation_extra_field():
    """FORBID-004: AIExplanationContract rejects unauthorized fields."""
    with pytest.raises(ValidationError):
        AIExplanationContract(
            result_id="r1",
            primary_reason="reason",
            detailed_narrative="narrative",
            bad_field="fail",
        )


def test_forbid_005_recommendation_extra_field():
    """FORBID-005: AIRecommendationContract rejects unauthorized fields."""
    with pytest.raises(ValidationError):
        AIRecommendationContract(
            id="rec-1",
            title="Rec",
            recommendation_type="outfit",
            content_object=get_ai_home_template().curated_recommendations[0].content_object,
            explanation=INITIAL_EXPLANATION,
            fabricated_score=99.9,
        )


def test_forbid_006_preferences_extra_field():
    """FORBID-006: AIPreferencesContract rejects unauthorized fields."""
    with pytest.raises(ValidationError):
        AIPreferencesContract(
            user_id="u1",
            unsupported_tweak=True,
        )


def test_forbid_007_feedback_extra_field():
    """FORBID-007: AIFeedbackContract rejects unauthorized fields."""
    with pytest.raises(ValidationError):
        AIFeedbackContract(
            id="fb-1",
            result_id="res-1",
            feedback_type=AIFeedbackType.HELPFUL,
            created_at="now",
            extra_metric="high",
        )


def test_forbid_008_request_contracts_extra_field():
    """FORBID-008: Request contracts reject unauthorized fields."""
    with pytest.raises(ValidationError):
        PostAIMessageRequestContract(
            content="Hello",
            unauthorized="injection",
        )

    with pytest.raises(ValidationError):
        PostAIFeedbackRequestContract(
            result_id="r1",
            feedback_type=AIFeedbackType.NOT_HELPFUL,
            rogue_attr="bad",
        )
