export type RecommendationStatus =
  | "RECOMMENDED"
  | "INSUFFICIENT_INFORMATION"
  | "POSSIBLE_ALTERNATIVES"
  | "NO_AVAILABLE_SIZE"
  | "UNSUPPORTED_CATEGORY"
  | "STALE_DATA"
  | "CONFLICTING_DATA";

export type MeasurementBasis = "BODY" | "GARMENT" | "UNKNOWN";

export type FitPreference =
  | "SLIM"
  | "REGULAR"
  | "RELAXED"
  | "OVERSIZED"
  | "NO_PREFERENCE";

export type FitFeedbackReason =
  | "SIZE_TOO_SMALL"
  | "SIZE_TOO_LARGE"
  | "FIT_TOO_TIGHT"
  | "FIT_TOO_LOOSE"
  | "LENGTH_TOO_SHORT"
  | "LENGTH_TOO_LONG"
  | "SIZE_CHART_INACCURATE"
  | "RECOMMENDATION_UNHELPFUL"
  | "OTHER";

export type PurchaseStatus = "PURCHASED" | "NOT_PURCHASED" | "UNKNOWN";

export interface RecommendedSizeDetail {
  variant_id: string;
  merchant_size_label: string;
}

export interface ConfidenceSummary {
  score: string | number;
  type: "INTERNAL_EVIDENCE_SCORE" | "CALIBRATED_PROBABILITY";
  display_to_shopper: boolean;
}

export interface FitEvidenceItem {
  label: string;
  status: string;
}

export interface FitEvidenceSummary {
  merchant_id?: string | null;
  merchant_product_id?: string | null;
  merchant_offer_id?: string | null;
  product_id: string;
  size_chart_id?: string | null;
  size_chart_revision?: number | null;
  size_system_code?: string | null;
  measurement_basis: MeasurementBasis;
  shopper_measurement_revision?: number | null;
  category_policy_version?: string | null;
  fit_algorithm_version: string;
  fit_preference_revision?: number | null;
  fit_preference_applied?: FitPreference | null;
  preference_evaluated: boolean;
  source_id?: string | null;
  source_revision?: string | null;
  taxonomy_version?: string;
  evidence_items?: FitEvidenceItem[];
}

export interface FitRecommendationRequest {
  product_id: string;
  merchant_offer_id?: string | null;
  variant_id?: string | null;
  category?: string | null;
}

export interface FitRecommendationResult {
  recommendation_id: string;
  status: RecommendationStatus;
  recommended_size: RecommendedSizeDetail | null;
  alternative_sizes: RecommendedSizeDetail[];
  confidence: ConfidenceSummary;
  reason_codes: string[];
  missing_information?: string[];
  explanations: string[];
  explanation: string;
  evidence: FitEvidenceSummary;
  is_valid: boolean;
  invalidated_reason?: string | null;
  fit_guaranteed: boolean;
  disclaimer_code: string;
  disclaimer: string;
  next_actions?: string[];
  created_at: string;
  expires_at?: string | null;
}

export interface FitFeedbackCreateRequest {
  reason: FitFeedbackReason;
  purchase_status?: PurchaseStatus;
  tried_on?: boolean;
  kept_item?: boolean | null;
  selected_different_size?: boolean;
  comment?: string | null;
}

export interface FitFeedbackResponse {
  feedback_id: string;
  recommendation_id: string;
  product_id: string;
  merchant_id?: string | null;
  size_chart_id?: string | null;
  size_chart_revision?: number | null;
  recommended_size?: string | null;
  reason: FitFeedbackReason;
  purchase_status: PurchaseStatus;
  tried_on: boolean;
  kept_item?: boolean | null;
  selected_different_size: boolean;
  feedback_basis: string;
  review_status: string;
  comment?: string | null;
  created_at: string;
}
