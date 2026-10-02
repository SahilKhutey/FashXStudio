"""Visual Design — Phase 12: AI / Intelligence Screens & Interaction System Schemas.

Establishes strict Pydantic v2 data contracts enforcing extra="forbid" via BaseContractModel.
Defines specifications for AI01 - AI09, session management, trust boundary models,
context chips, explainable recommendations, and multi-tier feedback (Sections 12.1 - 12.110).
"""

from enum import StrEnum
from typing import Any
from pydantic import Field
from schemas.base import BaseContractModel
from schemas.visual.fashion import VisualContentModel


# ---------------------------------------------------------------------------
# Enums & Taxonomies (Sections 12.2, 12.5, 12.11, 12.26, 12.37, 12.42)
# ---------------------------------------------------------------------------

class AIScreenId(StrEnum):
    """Authoritative screen identifiers for Phase 12 AI interfaces (Section 12.2)."""
    AI01_AI_HOME = "AI01"
    AI02_AI_FASHION_ASSISTANT = "AI02"
    AI03_AI_PRODUCT_ASSISTANT = "AI03"
    AI04_AI_STYLE_ASSISTANT = "AI04"
    AI05_AI_OUTFIT_RECOMMENDATION = "AI05"
    AI06_AI_SEARCH = "AI06"
    AI07_AI_RECOMMENDATION_DETAIL = "AI07"
    AI08_AI_RESULT_EXPLANATION = "AI08"
    AI09_AI_PREFERENCES = "AI09"


class AIMessageRole(StrEnum):
    """Origin entity of conversation message (Section 12.11, 12.40)."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class AIMessageState(StrEnum):
    """Operational lifecycle state of an AI interaction (Section 12.42)."""
    IDLE = "idle"
    SUBMITTING = "submitting"
    PROCESSING = "processing"
    STREAMING = "streaming"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


class AIProcessingStepState(StrEnum):
    """Deterministic progress status of a background intelligence step (Section 12.43)."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AIContentType(StrEnum):
    """Information classification boundary (Section 12.4, 12.5)."""
    PRODUCT_FACT = "product_fact"
    FASHION_CONTENT = "fashion_content"
    SYSTEM_RECOMMENDATION = "system_recommendation"
    AI_EXPLANATION = "ai_explanation"
    AI_GENERATED_CONTENT = "ai_generated_content"
    USER_INPUT = "user_input"
    USER_DECISION = "user_decision"


class AIConfidenceLevel(StrEnum):
    """Qualitative match confidence level without fake numerical certainty (Section 12.26)."""
    STRONG = "strong"
    POSSIBLE = "possible"
    LIMITED = "limited"


class AIFeedbackType(StrEnum):
    """User assessment of recommendation/response quality (Section 12.37)."""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"


class AIFeedbackReason(StrEnum):
    """Structured rationale for negative feedback (Section 12.37, 12.38)."""
    WRONG_STYLE = "wrong_style"
    WRONG_PRODUCT = "wrong_product"
    NOT_RELEVANT = "not_relevant"
    TOO_EXPENSIVE = "too_expensive"
    ALREADY_OWN = "already_own"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Core Context, Actions & Citations (Sections 12.12, 12.13, 12.59, 12.70)
# ---------------------------------------------------------------------------

class AIContextItemContract(BaseContractModel):
    """Transparent context item consumed by the AI system (Section 12.12, 12.13, 12.61)."""
    key: str
    label: str
    value: str
    is_removable: bool = Field(default=True)


class AICitationContract(BaseContractModel):
    """Authoritative source reference backing an AI assertion (Section 12.40, 12.70)."""
    source_id: str
    source_type: str
    title: str
    uri: str | None = Field(default=None)


class AIActionContract(BaseContractModel):
    """Explicit, verifiable action button mapping to supported workflows (Section 12.17, 12.59)."""
    action_id: str
    label: str
    action_type: str
    target_id: str | None = Field(default=None)
    payload: dict[str, Any] = Field(default_factory=dict)


class AIProcessingStepContract(BaseContractModel):
    """Granular observable intelligence operation (Section 12.43)."""
    id: str
    label: str
    state: AIProcessingStepState = Field(default=AIProcessingStepState.PENDING)
    detail: str | None = Field(default=None)


# ---------------------------------------------------------------------------
# Conversation & Session Models (Sections 12.9 - 12.11, 12.39 - 12.41)
# ---------------------------------------------------------------------------

class AIMessageContract(BaseContractModel):
    """Individual interaction record in an AI conversation (Section 12.11, 12.40)."""
    id: str
    role: AIMessageRole
    content: str
    created_at: str
    context_items: list[AIContextItemContract] = Field(default_factory=list)
    citations: list[AICitationContract] = Field(default_factory=list)
    suggested_actions: list[AIActionContract] = Field(default_factory=list)
    result_references: list[str] = Field(default_factory=list)
    state: AIMessageState = Field(default=AIMessageState.COMPLETE)


class AISessionContract(BaseContractModel):
    """Persisted conversation session tracking history and state (Section 12.39)."""
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[AIMessageContract] = Field(default_factory=list)
    context_items: list[AIContextItemContract] = Field(default_factory=list)
    state: AIMessageState = Field(default=AIMessageState.COMPLETE)


# ---------------------------------------------------------------------------
# Explanation, Recommendation & Preference Models (Sections 12.20 - 12.38)
# ---------------------------------------------------------------------------

class AIRecommendationFactorContract(BaseContractModel):
    """Verified factual contributor to an algorithmic suggestion (Section 12.25, 12.32)."""
    factor_name: str
    factor_value: str
    is_verified: bool = Field(default=True)


class AIExplanationContract(BaseContractModel):
    """Structured, transparent explanation of an AI recommendation (Section 12.23, 12.33)."""
    result_id: str
    primary_reason: str
    detailed_narrative: str
    matching_factors: list[AIRecommendationFactorContract] = Field(default_factory=list)
    context_used: list[str] = Field(default_factory=list)


class AIRecommendationContract(BaseContractModel):
    """Complete recommendation envelope tying content to transparent reasoning (Section 12.22, 12.24)."""
    id: str
    title: str
    recommendation_type: str
    content_object: VisualContentModel
    explanation: AIExplanationContract
    confidence: AIConfidenceLevel = Field(default=AIConfidenceLevel.STRONG)
    alternatives: list[VisualContentModel] = Field(default_factory=list)
    actions: list[AIActionContract] = Field(default_factory=list)


class AIPreferencesContract(BaseContractModel):
    """User-controlled AI customization and tuning parameters (Section 12.35, 12.36)."""
    user_id: str
    preferred_styles: list[str] = Field(default_factory=list)
    preferred_occasions: list[str] = Field(default_factory=list)
    budget_tier: str = Field(default="medium")
    allow_ai_personalization: bool = Field(default=True)
    auto_suggest_outfits: bool = Field(default=True)
    explanation_depth: str = Field(default="standard")


class AIFeedbackContract(BaseContractModel):
    """Explicit user evaluation of AI output (Section 12.37, 12.38)."""
    id: str
    result_id: str
    feedback_type: AIFeedbackType
    reason: AIFeedbackReason | None = Field(default=None)
    note: str | None = Field(default=None)
    created_at: str


class PostAIMessageRequestContract(BaseContractModel):
    """Payload to post a message into an AI session."""
    content: str
    context_items: list[AIContextItemContract] | None = Field(default=None)


class PostAIFeedbackRequestContract(BaseContractModel):
    """Payload to submit user evaluation of an AI output."""
    result_id: str
    feedback_type: AIFeedbackType
    reason: AIFeedbackReason | None = Field(default=None)
    note: str | None = Field(default=None)


# ---------------------------------------------------------------------------
# Screen Templates (AI01 – AI09, Sections 12.6 - 12.35)
# ---------------------------------------------------------------------------

class AIHomeTemplateSpecContract(BaseContractModel):
    """AI01: AI Home central intelligence entry point specification (Section 12.6, 12.7)."""
    screen_id: AIScreenId = Field(default=AIScreenId.AI01_AI_HOME)
    hero_title: str
    hero_subtitle: str
    quick_prompts: list[str] = Field(default_factory=list)
    suggested_tasks: list[AIActionContract] = Field(default_factory=list)
    recent_sessions: list[AISessionContract] = Field(default_factory=list)
    curated_recommendations: list[AIRecommendationContract] = Field(default_factory=list)


class AIAssistantTemplateSpecContract(BaseContractModel):
    """AI02: Multi-turn conversational fashion assistant specification (Section 12.9, 12.14)."""
    screen_id: AIScreenId = Field(default=AIScreenId.AI02_AI_FASHION_ASSISTANT)
    session: AISessionContract
    active_context: list[AIContextItemContract] = Field(default_factory=list)
    suggested_prompts: list[str] = Field(default_factory=list)


class AIProductAssistantTemplateSpecContract(BaseContractModel):
    """AI03: Product-specific Q&A with strict fact vs guidance separation (Section 12.15 - 12.17)."""
    screen_id: AIScreenId = Field(default=AIScreenId.AI03_AI_PRODUCT_ASSISTANT)
    product: VisualContentModel
    product_facts: dict[str, str] = Field(default_factory=dict)
    ai_guidance: str
    frequently_asked: list[str] = Field(default_factory=list)
    styling_suggestions: list[VisualContentModel] = Field(default_factory=list)
    similar_products: list[VisualContentModel] = Field(default_factory=list)


class AIStyleAssistantTemplateSpecContract(BaseContractModel):
    """AI04: Aesthetic recommendation with explainable matching (Section 12.18, 12.19)."""
    screen_id: AIScreenId = Field(default=AIScreenId.AI04_AI_STYLE_ASSISTANT)
    recommended_style: VisualContentModel
    why_it_fits: AIExplanationContract
    matching_looks: list[VisualContentModel] = Field(default_factory=list)
    suggested_products: list[VisualContentModel] = Field(default_factory=list)


class AIOutfitRecommendationTemplateSpecContract(BaseContractModel):
    """AI05: AI outfit recommendation with user editing controls (Section 12.20, 12.21)."""
    screen_id: AIScreenId = Field(default=AIScreenId.AI05_AI_OUTFIT_RECOMMENDATION)
    recommended_look: VisualContentModel
    explanation: AIExplanationContract
    constituent_items: list[VisualContentModel] = Field(default_factory=list)
    alternatives: list[VisualContentModel] = Field(default_factory=list)
    can_edit: bool = Field(default=True)


class AISearchTemplateSpecContract(BaseContractModel):
    """AI06: Natural language query search with intent interpretation (Section 12.27 - 12.31)."""
    screen_id: AIScreenId = Field(default=AIScreenId.AI06_AI_SEARCH)
    query: str
    interpreted_style: str | None = Field(default=None)
    interpreted_context: str | None = Field(default=None)
    interpreted_budget: str | None = Field(default=None)
    results: list[VisualContentModel] = Field(default_factory=list)
    total_results: int = Field(default=0, ge=0)
    processing_steps: list[AIProcessingStepContract] = Field(default_factory=list)


class AIRecommendationDetailTemplateSpecContract(BaseContractModel):
    """AI07: Deep dive into an individual recommendation (Section 12.24)."""
    screen_id: AIScreenId = Field(default=AIScreenId.AI07_AI_RECOMMENDATION_DETAIL)
    recommendation: AIRecommendationContract
    context_used: list[AIContextItemContract] = Field(default_factory=list)
    supporting_products: list[VisualContentModel] = Field(default_factory=list)
    alternatives: list[VisualContentModel] = Field(default_factory=list)


class AIResultExplanationTemplateSpecContract(BaseContractModel):
    """AI08: Dedicated why this result explanation canvas (Section 12.32 - 12.34)."""
    screen_id: AIScreenId = Field(default=AIScreenId.AI08_AI_RESULT_EXPLANATION)
    result_id: str
    target_item: VisualContentModel
    explanation: AIExplanationContract
    contributing_factors: list[AIRecommendationFactorContract] = Field(default_factory=list)
    user_feedback: AIFeedbackContract | None = Field(default=None)


class AIPreferencesTemplateSpecContract(BaseContractModel):
    """AI09: AI tuning preferences control canvas (Section 12.35, 12.36)."""
    screen_id: AIScreenId = Field(default=AIScreenId.AI09_AI_PREFERENCES)
    preferences: AIPreferencesContract
    available_styles: list[str] = Field(default_factory=list)
    available_occasions: list[str] = Field(default_factory=list)
    budget_tiers: list[str] = Field(default_factory=list)
