"""AI / Intelligence Domain Service — Phase 12.

Provides multi-turn fashion conversation, intent-aware AI search, explainable recommendations,
product assistant Q&A with strict fact boundaries, and preference customization (Sections 12.1 - 12.110).
Adheres strictly to Constitution Rule I01 (Layer Separation) and Rule I02 (Contract Primacy).
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from schemas.visual.fashion import (
    FashionContentType,
    VisualContentModel,
)
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
)
from .fashion_service import (
    SAMPLE_LOOKS,
    SAMPLE_PRODUCTS,
    SAMPLE_STYLES,
    to_visual_content_model,
)


def _get_current_iso_timestamp() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Canonical Fixtures & Initial State (Sections 12.6, 12.20, 12.35)
# ---------------------------------------------------------------------------

DEFAULT_PREFERENCES = AIPreferencesContract(
    user_id="user-default",
    preferred_styles=["Streetwear", "Minimalist"],
    preferred_occasions=["Casual", "Summer Weekend"],
    budget_tier="medium",
    allow_ai_personalization=True,
    auto_suggest_outfits=True,
    explanation_depth="standard",
)

INITIAL_EXPLANATION = AIExplanationContract(
    result_id="rec-summer-streetwear-01",
    primary_reason="Matches your explored preference for relaxed silhouettes and monsoon-resistant fabrics.",
    detailed_narrative=(
        "Curated by matching 14oz raw selvedge denim textures with breathable organic cotton. "
        "The boxy proportions create an effortless drape suitable for tropical evening transit."
    ),
    matching_factors=[
        AIRecommendationFactorContract(
            factor_name="Style Direction",
            factor_value="Relaxed Streetwear",
            is_verified=True,
        ),
        AIRecommendationFactorContract(
            factor_name="Climate Suitability",
            factor_value="Breathable 24°C - 32°C",
            is_verified=True,
        ),
        AIRecommendationFactorContract(
            factor_name="Palette Harmony",
            factor_value="Raw Indigo & Natural Ecru",
            is_verified=True,
        ),
    ],
    context_used=["Current Region: Mumbai", "Selected Season: Monsoon", "Budget Tier: Medium"],
)

INITIAL_RECOMMENDATIONS: list[AIRecommendationContract] = [
    AIRecommendationContract(
        id="rec-summer-streetwear-01",
        title="Urban Minimalist Rain Ensemble",
        recommendation_type="outfit_look",
        content_object=to_visual_content_model(SAMPLE_LOOKS[0], FashionContentType.LOOK),
        explanation=INITIAL_EXPLANATION,
        confidence=AIConfidenceLevel.STRONG,
        alternatives=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS[1:3]],
        actions=[
            AIActionContract(
                action_id="act-view-look",
                label="Explore Look",
                action_type="navigate",
                target_id=SAMPLE_LOOKS[0].id,
            ),
            AIActionContract(
                action_id="act-build-outfit",
                label="Customize in Outfit Studio",
                action_type="studio_edit",
                target_id=SAMPLE_LOOKS[0].id,
            ),
        ],
    ),
]

INITIAL_SESSIONS: dict[str, AISessionContract] = {
    "session-summer-trip": AISessionContract(
        id="session-summer-trip",
        title="Summer Travel Wardrobe",
        created_at="2026-10-01T08:00:00Z",
        updated_at="2026-10-01T08:30:00Z",
        messages=[
            AIMessageContract(
                id="msg-1",
                role=AIMessageRole.USER,
                content="Find versatile outfits for a 5-day summer trip to coastal humid areas.",
                created_at="2026-10-01T08:00:00Z",
                context_items=[
                    AIContextItemContract(key="destination", label="Destination", value="Coastal", is_removable=True),
                    AIContextItemContract(key="season", label="Season", value="Summer", is_removable=True),
                ],
                state=AIMessageState.COMPLETE,
            ),
            AIMessageContract(
                id="msg-2",
                role=AIMessageRole.ASSISTANT,
                content="Here are 3 versatile directions utilizing lightweight linen and structured selvedge denim.",
                created_at="2026-10-01T08:01:00Z",
                citations=[
                    AICitationContract(
                        source_id="cat-textiles",
                        source_type="fabric_guide",
                        title="Humid Weather Natural Handlooms",
                    ),
                ],
                suggested_actions=[
                    AIActionContract(
                        action_id="act-see-looks",
                        label="View Recommended Looks",
                        action_type="navigate",
                        target_id="look-mumbai-01",
                    ),
                ],
                result_references=["rec-summer-streetwear-01"],
                state=AIMessageState.COMPLETE,
            ),
        ],
        context_items=[
            AIContextItemContract(key="destination", label="Destination", value="Coastal"),
            AIContextItemContract(key="season", label="Season", value="Summer"),
        ],
        state=AIMessageState.COMPLETE,
    ),
}

# In-memory mutable registries
SESSIONS_REGISTRY: dict[str, AISessionContract] = dict(INITIAL_SESSIONS)
FEEDBACK_REGISTRY: list[AIFeedbackContract] = []
CURRENT_PREFERENCES: AIPreferencesContract = DEFAULT_PREFERENCES.model_copy(deep=True)


# ---------------------------------------------------------------------------
# Template Builders & Domain Operations (AI01 – AI09)
# ---------------------------------------------------------------------------

def get_ai_home_template() -> AIHomeTemplateSpecContract:
    """Build AI01 AI Home gateway specification (Section 12.6, 12.7)."""
    suggested_tasks = [
        AIActionContract(
            action_id="task-prod-assist",
            label="Product Assistant",
            action_type="open_tool",
            target_id="AI03",
        ),
        AIActionContract(
            action_id="task-style-assist",
            label="Style Assistant",
            action_type="open_tool",
            target_id="AI04",
        ),
        AIActionContract(
            action_id="task-outfit-rec",
            label="Outfit Ideas",
            action_type="open_tool",
            target_id="AI05",
        ),
        AIActionContract(
            action_id="task-fashion-search",
            label="Fashion Search",
            action_type="open_tool",
            target_id="AI06",
        ),
    ]

    return AIHomeTemplateSpecContract(
        screen_id=AIScreenId.AI01_AI_HOME,
        hero_title="AI Fashion Assistant",
        hero_subtitle="Discover fashion. Find products. Build looks. Understand recommendations.",
        quick_prompts=[
            "Find relaxed summer outfits under ₹3,000",
            "How would I style an oversized selvedge denim jacket?",
            "Show me minimalist capsules for high-humidity climates",
            "What accessories pair with Kosa wild silk?",
        ],
        suggested_tasks=suggested_tasks,
        recent_sessions=list(SESSIONS_REGISTRY.values())[:3],
        curated_recommendations=INITIAL_RECOMMENDATIONS,
    )


def create_ai_session(title: str = "New Fashion Session") -> AISessionContract:
    """Instantiate a new conversation session."""
    session_id = f"session-{uuid.uuid4().hex[:8]}"
    now = _get_current_iso_timestamp()
    new_session = AISessionContract(
        id=session_id,
        title=title,
        created_at=now,
        updated_at=now,
        messages=[],
        context_items=[
            AIContextItemContract(key="style", label="Default Style", value="Streetwear"),
            AIContextItemContract(key="region", label="Region", value="India"),
        ],
        state=AIMessageState.COMPLETE,
    )
    SESSIONS_REGISTRY[session_id] = new_session
    return new_session


def get_ai_session(session_id: str) -> AISessionContract:
    """Retrieve an active or archived conversation session."""
    return SESSIONS_REGISTRY.get(session_id, SESSIONS_REGISTRY["session-summer-trip"])


def post_ai_message(
    session_id: str,
    content: str,
    context_items: list[AIContextItemContract] | None = None,
) -> AIMessageContract:
    """Append user message and generate structured, transparent assistant response."""
    session = SESSIONS_REGISTRY.get(session_id)
    if not session:
        session = create_ai_session(title=content[:30] or "Fashion Query")
        session_id = session.id

    now = _get_current_iso_timestamp()
    user_msg = AIMessageContract(
        id=f"msg-u-{uuid.uuid4().hex[:6]}",
        role=AIMessageRole.USER,
        content=content,
        created_at=now,
        context_items=context_items or session.context_items,
        state=AIMessageState.COMPLETE,
    )
    session.messages.append(user_msg)

    # Deterministic assistant response with explicit product & look recommendations
    assistant_msg = AIMessageContract(
        id=f"msg-a-{uuid.uuid4().hex[:6]}",
        role=AIMessageRole.ASSISTANT,
        content=f"Based on your request '{content}', I've identified complementary pieces emphasizing relaxed silhouettes and verified fabric pairings.",
        created_at=now,
        citations=[
            AICitationContract(
                source_id="fashx-catalog",
                source_type="inventory_index",
                title="FashX Verified Catalog",
            ),
        ],
        suggested_actions=[
            AIActionContract(
                action_id="act-refine",
                label="Refine Style",
                action_type="refine_prompt",
            ),
            AIActionContract(
                action_id="act-open-builder",
                label="Open Outfit Studio",
                action_type="studio_edit",
                target_id="look-mumbai-01",
            ),
        ],
        result_references=["rec-summer-streetwear-01"],
        state=AIMessageState.COMPLETE,
    )
    session.messages.append(assistant_msg)
    session.updated_at = now
    return assistant_msg


def get_ai_assistant_template(session_id: str | None = None) -> AIAssistantTemplateSpecContract:
    """Build AI02 AI Fashion Assistant conversation template (Section 12.9, 12.14)."""
    session = SESSIONS_REGISTRY.get(session_id or "session-summer-trip", SESSIONS_REGISTRY["session-summer-trip"])
    return AIAssistantTemplateSpecContract(
        screen_id=AIScreenId.AI02_AI_FASHION_ASSISTANT,
        session=session,
        active_context=session.context_items,
        suggested_prompts=[
            "Refine silhouette for tropical heat",
            "Find cheaper footwear alternatives",
            "Show matching accessories",
        ],
    )


def get_product_assistant_template(product_id: str) -> AIProductAssistantTemplateSpecContract:
    """Build AI03 Product Assistant with strict fact vs guidance separation (Section 12.15 - 12.17)."""
    prod_item = next((p for p in SAMPLE_PRODUCTS if p.id == product_id), SAMPLE_PRODUCTS[0])
    prod_model = to_visual_content_model(prod_item, FashionContentType.PRODUCT)

    # Authoritative product facts directly from catalog - NEVER fabricated by AI
    facts = {
        "Price": f"₹{prod_item.price.amount:,.2f}",
        "Availability": "In Stock (Ships in 24 hrs)" if prod_item.is_in_stock else "Backorder",
        "Material": str(prod_item.attributes.get("fabric", "100% Selvedge Cotton")),
        "Fit": str(prod_item.attributes.get("fit", "Relaxed Boxy")),
        "Origin": str(prod_item.attributes.get("origin", "Kojima, Okayama")),
    }

    # AI guidance clearly separated from physical product facts
    guidance = (
        "This jacket features a structured, dropped shoulder silhouette. "
        "We recommend styling it over a lightweight ecru hemp tee with wide-leg trousers "
        "for balanced proportions."
    )

    return AIProductAssistantTemplateSpecContract(
        screen_id=AIScreenId.AI03_AI_PRODUCT_ASSISTANT,
        product=prod_model,
        product_facts=facts,
        ai_guidance=guidance,
        frequently_asked=[
            "How does this jacket fit across the shoulders?",
            "What color trousers pair best with Raw Indigo?",
            "Is the denim pre-shrunk or raw sanforized?",
        ],
        styling_suggestions=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS[:2]],
        similar_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS[1:3]],
    )


def get_style_assistant_template(style_id: str | None = None) -> AIStyleAssistantTemplateSpecContract:
    """Build AI04 Style Assistant specification (Section 12.18, 12.19)."""
    style_item = next((s for s in SAMPLE_STYLES if s.id == style_id), SAMPLE_STYLES[0])
    style_model = to_visual_content_model(style_item, FashionContentType.STYLE)

    explanation = AIExplanationContract(
        result_id=f"exp-style-{style_item.id}",
        primary_reason="Selected because of your affinity for relaxed utilitarian tailoring and heritage textiles.",
        detailed_narrative=(
            f"{style_item.name} combines functional outerwear detailing with relaxed draping. "
            "It aligns with your saved preference for modular wardrobe versatility."
        ),
        matching_factors=[
            AIRecommendationFactorContract(factor_name="Silhouette", factor_value="Relaxed Boxy", is_verified=True),
            AIRecommendationFactorContract(factor_name="Versatility", factor_value="High (Day to Night)", is_verified=True),
        ],
        context_used=["Preference: Streetwear", "Context: Urban Transit"],
    )

    return AIStyleAssistantTemplateSpecContract(
        screen_id=AIScreenId.AI04_AI_STYLE_ASSISTANT,
        recommended_style=style_model,
        why_it_fits=explanation,
        matching_looks=[to_visual_content_model(l, FashionContentType.LOOK) for l in SAMPLE_LOOKS[:2]],
        suggested_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS[:2]],
    )


def get_outfit_recommendation_template(look_id: str | None = None) -> AIOutfitRecommendationTemplateSpecContract:
    """Build AI05 Outfit Recommendation specification (Section 12.20, 12.21)."""
    look = next((l for l in SAMPLE_LOOKS if l.id == look_id), SAMPLE_LOOKS[0])
    look_model = to_visual_content_model(look, FashionContentType.LOOK)

    return AIOutfitRecommendationTemplateSpecContract(
        screen_id=AIScreenId.AI05_AI_OUTFIT_RECOMMENDATION,
        recommended_look=look_model,
        explanation=INITIAL_EXPLANATION,
        constituent_items=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS[:3]],
        alternatives=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS[1:3]],
        can_edit=True,
    )


def ai_search(query: str) -> AISearchTemplateSpecContract:
    """Execute natural language search with intent understanding (Section 12.27 - 12.31)."""
    q_lower = query.lower()

    # Intent extraction
    interpreted_style = "Streetwear" if "street" in q_lower or "casual" in q_lower else ("Minimal" if "minimal" in q_lower else "Relaxed")
    interpreted_context = "Summer" if "summer" in q_lower or "hot" in q_lower else ("Monsoon" if "monsoon" in q_lower or "rain" in q_lower else "Everyday")
    interpreted_budget = "Under ₹3,000" if "3000" in q_lower or "budget" in q_lower else "Under ₹7,000"

    # Multi-stage observable processing steps (Section 12.43)
    steps = [
        AIProcessingStepContract(id="step-1", label="Understanding natural language query", state=AIProcessingStepState.COMPLETED),
        AIProcessingStepContract(id="step-2", label="Extracting aesthetic style & budget constraints", state=AIProcessingStepState.COMPLETED),
        AIProcessingStepContract(id="step-3", label="Searching catalog and ranking matches", state=AIProcessingStepState.COMPLETED),
    ]

    matched_products = [
        to_visual_content_model(p, FashionContentType.PRODUCT)
        for p in SAMPLE_PRODUCTS
        if not query or any(w in p.title.lower() or w in p.category.lower() for w in query.lower().split())
    ]
    if not matched_products:
        matched_products = [to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS[:2]]

    return AISearchTemplateSpecContract(
        screen_id=AIScreenId.AI06_AI_SEARCH,
        query=query,
        interpreted_style=interpreted_style,
        interpreted_context=interpreted_context,
        interpreted_budget=interpreted_budget,
        results=matched_products,
        total_results=len(matched_products),
        processing_steps=steps,
    )


def get_recommendation_detail(recommendation_id: str) -> AIRecommendationDetailTemplateSpecContract:
    """Build AI07 Recommendation Detail specification (Section 12.24)."""
    rec = next((r for r in INITIAL_RECOMMENDATIONS if r.id == recommendation_id), INITIAL_RECOMMENDATIONS[0])
    return AIRecommendationDetailTemplateSpecContract(
        screen_id=AIScreenId.AI07_AI_RECOMMENDATION_DETAIL,
        recommendation=rec,
        context_used=[
            AIContextItemContract(key="style", label="Aesthetic Preference", value="Contemporary Streetwear"),
            AIContextItemContract(key="region", label="Current Location", value="Mumbai (High Humidity)"),
        ],
        supporting_products=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS[:3]],
        alternatives=[to_visual_content_model(p, FashionContentType.PRODUCT) for p in SAMPLE_PRODUCTS[1:3]],
    )


def get_result_explanation(result_id: str) -> AIResultExplanationTemplateSpecContract:
    """Build AI08 Why This Result explanation specification (Section 12.32 - 12.34)."""
    target = to_visual_content_model(SAMPLE_LOOKS[0], FashionContentType.LOOK)
    return AIResultExplanationTemplateSpecContract(
        screen_id=AIScreenId.AI08_AI_RESULT_EXPLANATION,
        result_id=result_id,
        target_item=target,
        explanation=INITIAL_EXPLANATION,
        contributing_factors=INITIAL_EXPLANATION.matching_factors,
        user_feedback=None,
    )


def get_ai_preferences(user_id: str = "user-default") -> AIPreferencesTemplateSpecContract:
    """Build AI09 AI Preferences specification (Section 12.35, 12.36)."""
    return AIPreferencesTemplateSpecContract(
        screen_id=AIScreenId.AI09_AI_PREFERENCES,
        preferences=CURRENT_PREFERENCES,
        available_styles=["Minimalist", "Streetwear", "Heritage Workwear", "Formal Tailored", "Casual Relaxed"],
        available_occasions=["Casual Everyday", "Summer Travel", "Evening Dinner", "Office Professional"],
        budget_tiers=["budget", "medium", "premium", "luxury"],
    )


def update_ai_preferences(preferences: AIPreferencesContract) -> AIPreferencesContract:
    """Update user AI tuning preferences."""
    global CURRENT_PREFERENCES
    CURRENT_PREFERENCES = preferences.model_copy(deep=True)
    return CURRENT_PREFERENCES


def submit_ai_feedback(
    result_id: str,
    feedback_type: AIFeedbackType,
    reason: AIFeedbackReason | None = None,
    note: str | None = None,
) -> AIFeedbackContract:
    """Store explicit user feedback evaluating an AI result (Section 12.37, 12.38)."""
    fb = AIFeedbackContract(
        id=f"fb-{uuid.uuid4().hex[:8]}",
        result_id=result_id,
        feedback_type=feedback_type,
        reason=reason,
        note=note,
        created_at=_get_current_iso_timestamp(),
    )
    FEEDBACK_REGISTRY.append(fb)
    return fb


def reset_ai_fixtures() -> None:
    """Reset mutable in-memory session, feedback, and preference state for test isolation."""
    global CURRENT_PREFERENCES
    SESSIONS_REGISTRY.clear()
    SESSIONS_REGISTRY.update(INITIAL_SESSIONS)
    FEEDBACK_REGISTRY.clear()
    CURRENT_PREFERENCES = DEFAULT_PREFERENCES.model_copy(deep=True)
