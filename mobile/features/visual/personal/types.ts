/**
 * Visual Design — Phase 13: Profile, Personalization & Saved Experience TypeScript Interfaces.
 * Mirrors Pydantic v2 schemas defined in schemas/visual/personal.py.
 */

export type PersonalScreenId =
  | "PR01"
  | "PR02"
  | "PR03"
  | "PR04"
  | "PR05"
  | "PR06"
  | "PR07"
  | "PR08"
  | "PR09"
  | "PR10"
  | "PR11";

export type PersonalState =
  | "loading"
  | "loaded"
  | "empty"
  | "partial"
  | "error"
  | "saving"
  | "saved"
  | "unsaved_changes"
  | "restricted"
  | "session_expired";

export type ActivityEntityType =
  | "product"
  | "look"
  | "fashion"
  | "trend"
  | "collection";

export type ActivityAction =
  | "view"
  | "search"
  | "save"
  | "unsave"
  | "open"
  | "edit"
  | "shop";

export type SavedFashionContentType =
  | "story"
  | "article"
  | "collection"
  | "editorial"
  | "trend"
  | "brand";

export type SavedItemType = "product" | "look" | "fashion" | "wishlist";

export interface ActivityContract {
  entity_id: string;
  entity_type: ActivityEntityType;
  action: ActivityAction;
  title: string;
  subtitle?: string | null;
  image_url?: string | null;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface SavedProductContract {
  id: string;
  product_id: string;
  brand: string;
  name: string;
  price: number;
  currency: string;
  image_url?: string | null;
  is_saved: boolean;
  saved_state_label: string;
  availability: "in_stock" | "low_stock" | "out_of_stock" | string;
  saved_at: string;
}

export interface SavedLookContract {
  id: string;
  look_id: string;
  title: string;
  style: string;
  image_url?: string | null;
  collection_id?: string | null;
  items_count: number;
  supported_actions: string[];
  saved_at: string;
}

export interface SavedFashionContract {
  id: string;
  content_id: string;
  content_type: SavedFashionContentType;
  title: string;
  author_or_brand?: string | null;
  image_url?: string | null;
  saved_at: string;
}

export interface WishlistItemContract {
  id: string;
  product_id: string;
  brand: string;
  name: string;
  price: number;
  currency: string;
  image_url?: string | null;
  availability: "in_stock" | "out_of_stock" | "discontinued" | string;
  is_available: boolean;
  availability_notice?: string | null;
  alternative_product_id?: string | null;
  added_at: string;
}

export interface PersonalCollectionContract {
  id: string;
  name: string;
  description?: string | null;
  item_count: number;
  cover_image_url?: string | null;
  created_at: string;
}

export interface ExplicitPreferencesContract {
  styles: string[];
  categories: string[];
  colors: string[];
  fits: string[];
  materials: string[];
  contexts: string[];
}

export interface InferredPreferencesContract {
  frequently_viewed_styles: string[];
  frequently_viewed_categories: string[];
  frequently_viewed_colors: string[];
  observation_notice: string;
}

export interface SavedSummaryContract {
  products_count: number;
  looks_count: number;
  fashion_count: number;
  wishlist_count: number;
  collections_count: number;
}

export interface RecommendationPreferencesContract {
  personalized_recommendations: boolean;
  use_style_preferences: boolean;
  use_regional_context: boolean;
  transparency_signals: string[];
}

export interface RegionalPreferencesContract {
  preferred_country: string;
  preferred_state?: string | null;
  preferred_city?: string | null;
  regional_discovery_enabled: boolean;
  delivery_region: string;
  disclaimer: string;
}

export interface PersonalAIPreferencesContract {
  ai_recommendations_enabled: boolean;
  ai_personalization_enabled: boolean;
  ai_interaction_mode: string;
  ai_context_permitted: string[];
}

export interface AccountSettingsContract {
  user_id: string;
  email: string;
  display_name: string;
  notifications_enabled: boolean;
  privacy_level: string;
  two_factor_auth: boolean;
  activity_history_retention: string;
  categories: string[];
}

export interface ProfileTemplateSpecContract {
  screen_id: PersonalScreenId;
  user_id: string;
  display_name: string;
  avatar_url?: string | null;
  bio?: string | null;
  style_tags: string[];
  saved_summary: SavedSummaryContract;
  preferences_preview: string[];
  recent_activity_preview: ActivityContract[];
  regional_context: RegionalPreferencesContract;
  state: PersonalState;
}

export interface PersonalDashboardTemplateSpecContract {
  screen_id: PersonalScreenId;
  welcome_title: string;
  continue_exploring: Record<string, any>[];
  recommended_products: SavedProductContract[];
  recommended_looks: SavedLookContract[];
  saved_preview: Record<string, any>[];
  recently_viewed: ActivityContract[];
  regional_highlights: Record<string, any>[];
  ai_suggestions: Record<string, any>[];
  module_states: Record<string, PersonalState>;
  state: PersonalState;
}

export interface SavedProductsTemplateSpecContract {
  screen_id: PersonalScreenId;
  title: string;
  total_count: number;
  items: SavedProductContract[];
  active_filter?: string | null;
  active_sort: string;
  state: PersonalState;
}

export interface SavedLooksTemplateSpecContract {
  screen_id: PersonalScreenId;
  title: string;
  total_count: number;
  collections: PersonalCollectionContract[];
  items: SavedLookContract[];
  active_collection?: string | null;
  state: PersonalState;
}

export interface SavedFashionTemplateSpecContract {
  screen_id: PersonalScreenId;
  title: string;
  active_tab: string;
  available_tabs: string[];
  items: SavedFashionContract[];
  total_count: number;
  state: PersonalState;
}

export interface WishlistTemplateSpecContract {
  screen_id: PersonalScreenId;
  title: string;
  items: WishlistItemContract[];
  total_count: number;
  available_count: number;
  unavailable_count: number;
  state: PersonalState;
}

export interface RecentlyViewedTemplateSpecContract {
  screen_id: PersonalScreenId;
  title: string;
  items: ActivityContract[];
  total_count: number;
  active_filter?: string | null;
  can_clear_history: boolean;
  state: PersonalState;
}

export interface PreferencesTemplateSpecContract {
  screen_id: PersonalScreenId;
  title: string;
  explicit_preferences: ExplicitPreferencesContract;
  inferred_preferences: InferredPreferencesContract;
  available_styles: string[];
  available_categories: string[];
  available_colors: string[];
  available_fits: string[];
  available_materials: string[];
  available_contexts: string[];
  has_unsaved_changes: boolean;
  state: PersonalState;
}

export interface RecommendationPreferencesTemplateSpecContract {
  screen_id: PersonalScreenId;
  title: string;
  settings: RecommendationPreferencesContract;
  transparency_explanation: string;
  can_reset_personalization: boolean;
  state: PersonalState;
}

export interface RegionalPreferencesTemplateSpecContract {
  screen_id: PersonalScreenId;
  title: string;
  settings: RegionalPreferencesContract;
  available_countries: string[];
  available_regions: string[];
  disclaimer: string;
  state: PersonalState;
}

export interface AccountSettingsTemplateSpecContract {
  screen_id: PersonalScreenId;
  title: string;
  settings: AccountSettingsContract;
  categories: string[];
  has_unsaved_changes: boolean;
  state: PersonalState;
}
