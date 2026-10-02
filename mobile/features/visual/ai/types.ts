/**
 * Visual Design — Phase 12: AI / Intelligence TypeScript Interfaces.
 * Mirrors Pydantic v2 schemas defined in schemas/visual/ai.py.
 */

import { VisualContentModel } from "../fashion/types";

export type AIScreenId =
  | "AI01"
  | "AI02"
  | "AI03"
  | "AI04"
  | "AI05"
  | "AI06"
  | "AI07"
  | "AI08"
  | "AI09";

export type AIMessageRole = "user" | "assistant" | "system" | "tool";

export type AIMessageState =
  | "idle"
  | "submitting"
  | "processing"
  | "streaming"
  | "complete"
  | "error"
  | "cancelled";

export type AIProcessingStepState = "pending" | "running" | "completed" | "failed";

export type AIContentType =
  | "product_fact"
  | "fashion_content"
  | "system_recommendation"
  | "ai_explanation"
  | "ai_generated_content"
  | "user_input"
  | "user_decision";

export type AIConfidenceLevel = "strong" | "possible" | "limited";

export type AIFeedbackType = "helpful" | "not_helpful";

export type AIFeedbackReason =
  | "wrong_style"
  | "wrong_product"
  | "not_relevant"
  | "too_expensive"
  | "already_own"
  | "other";

export interface AIContextItemContract {
  key: string;
  label: string;
  value: string;
  is_removable?: boolean;
}

export interface AICitationContract {
  source_id: string;
  source_type: string;
  title: string;
  uri?: string | null;
}

export interface AIActionContract {
  action_id: string;
  label: string;
  action_type: string;
  target_id?: string | null;
  payload?: Record<string, any>;
}

export interface AIProcessingStepContract {
  id: string;
  label: string;
  state?: AIProcessingStepState;
  detail?: string | null;
}

export interface AIMessageContract {
  id: string;
  role: AIMessageRole;
  content: string;
  created_at: string;
  context_items?: AIContextItemContract[];
  citations?: AICitationContract[];
  suggested_actions?: AIActionContract[];
  result_references?: string[];
  state?: AIMessageState;
}

export interface AISessionContract {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: AIMessageContract[];
  context_items?: AIContextItemContract[];
  state?: AIMessageState;
}

export interface AIRecommendationFactorContract {
  factor_name: string;
  factor_value: string;
  is_verified?: boolean;
}

export interface AIExplanationContract {
  result_id: string;
  primary_reason: string;
  detailed_narrative: string;
  matching_factors?: AIRecommendationFactorContract[];
  context_used?: string[];
}

export interface AIRecommendationContract {
  id: string;
  title: string;
  recommendation_type: string;
  content_object: VisualContentModel;
  explanation: AIExplanationContract;
  confidence?: AIConfidenceLevel;
  alternatives?: VisualContentModel[];
  actions?: AIActionContract[];
}

export interface AIPreferencesContract {
  user_id: string;
  preferred_styles?: string[];
  preferred_occasions?: string[];
  budget_tier?: string;
  allow_ai_personalization?: boolean;
  auto_suggest_outfits?: boolean;
  explanation_depth?: string;
}

export interface AIFeedbackContract {
  id: string;
  result_id: string;
  feedback_type: AIFeedbackType;
  reason?: AIFeedbackReason | null;
  note?: string | null;
  created_at: string;
}

export interface PostAIMessageRequestContract {
  content: string;
  context_items?: AIContextItemContract[] | null;
}

export interface PostAIFeedbackRequestContract {
  result_id: string;
  feedback_type: AIFeedbackType;
  reason?: AIFeedbackReason | null;
  note?: string | null;
}

// ---------------------------------------------------------------------------
// Template Specification Contracts (AI01 – AI09)
// ---------------------------------------------------------------------------

export interface AIHomeTemplateSpecContract {
  screen_id: AIScreenId;
  hero_title: string;
  hero_subtitle: string;
  quick_prompts?: string[];
  suggested_tasks?: AIActionContract[];
  recent_sessions?: AISessionContract[];
  curated_recommendations?: AIRecommendationContract[];
}

export interface AIAssistantTemplateSpecContract {
  screen_id: AIScreenId;
  session: AISessionContract;
  active_context?: AIContextItemContract[];
  suggested_prompts?: string[];
}

export interface AIProductAssistantTemplateSpecContract {
  screen_id: AIScreenId;
  product: VisualContentModel;
  product_facts?: Record<string, string>;
  ai_guidance: string;
  frequently_asked?: string[];
  styling_suggestions?: VisualContentModel[];
  similar_products?: VisualContentModel[];
}

export interface AIStyleAssistantTemplateSpecContract {
  screen_id: AIScreenId;
  recommended_style: VisualContentModel;
  why_it_fits: AIExplanationContract;
  matching_looks?: VisualContentModel[];
  suggested_products?: VisualContentModel[];
}

export interface AIOutfitRecommendationTemplateSpecContract {
  screen_id: AIScreenId;
  recommended_look: VisualContentModel;
  explanation: AIExplanationContract;
  constituent_items?: VisualContentModel[];
  alternatives?: VisualContentModel[];
  can_edit?: boolean;
}

export interface AISearchTemplateSpecContract {
  screen_id: AIScreenId;
  query: string;
  interpreted_style?: string | null;
  interpreted_context?: string | null;
  interpreted_budget?: string | null;
  results?: VisualContentModel[];
  total_results?: number;
  processing_steps?: AIProcessingStepContract[];
}

export interface AIRecommendationDetailTemplateSpecContract {
  screen_id: AIScreenId;
  recommendation: AIRecommendationContract;
  context_used?: AIContextItemContract[];
  supporting_products?: VisualContentModel[];
  alternatives?: VisualContentModel[];
}

export interface AIResultExplanationTemplateSpecContract {
  screen_id: AIScreenId;
  result_id: string;
  target_item: VisualContentModel;
  explanation: AIExplanationContract;
  contributing_factors?: AIRecommendationFactorContract[];
  user_feedback?: AIFeedbackContract | null;
}

export interface AIPreferencesTemplateSpecContract {
  screen_id: AIScreenId;
  preferences: AIPreferencesContract;
  available_styles?: string[];
  available_occasions?: string[];
  budget_tiers?: string[];
}
