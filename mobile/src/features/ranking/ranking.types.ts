export type RankingReasonCode =
  | "CATEGORY_MATCH"
  | "STYLE_MATCH"
  | "COLOR_MATCH"
  | "PRICE_MATCH"
  | "SIZE_AVAILABLE"
  | "VISUAL_SIMILARITY"
  | "FEEDBACK_MATCH"
  | "QUALITY_VALIDATED";

export type SizeAvailabilityState =
  | "AVAILABLE"
  | "UNAVAILABLE"
  | "UNKNOWN"
  | "NOT_APPLICABLE";

export type FeedbackType =
  | "LIKE"
  | "DISLIKE"
  | "SAVE"
  | "REMOVE_SAVED"
  | "NOT_INTERESTED";

export interface RankingContextPayload {
  query?: string | null;
  category_id?: string | null;
  selected_size?: string | null;
  min_price?: number | string | null;
  max_price?: number | string | null;
  currency?: string;
  reference_image_asset_id?: string | null;
  reference_product_id?: string | null;
  require_selected_size?: boolean;
  page?: number;
  page_size?: number;
}

export interface RankedProductItem {
  product_id: string;
  merchant_offer_id: string;
  title: string;
  category_id: string;
  price?: number | string | null;
  currency?: string | null;
  position: number;
  ranking_score: number;
  availability: string;
  size_availability: SizeAvailabilityState;
  selected_size_available: boolean;
  reasons: RankingReasonCode[];
  reason_labels: string[];
  is_sponsored: boolean;
  availability_verified_at?: string | null;
  ranking_version: string;
}

export interface RankedProductsResponse {
  request_id: string;
  ranking_version: string;
  config_version: string;
  taxonomy_version: string;
  cache_hit: boolean;
  results: RankedProductItem[];
  pagination: {
    page: number;
    page_size: number;
    total_eligible: number;
    has_more: boolean;
  };
}
