/**
 * FashXStudio Outfit, Styling & Fashion Experience System TypeScript Interfaces — Phase 10.
 *
 * Mirrors schemas/visual/styling.py Pydantic v2 data contracts.
 */

import { VisualContentModel } from "../types";

export type StylingScreenId =
  | "ST01"
  | "ST02"
  | "ST03"
  | "ST04"
  | "ST05"
  | "ST06"
  | "ST07"
  | "ST08"
  | "ST09";

export type SlotCategory =
  | "top"
  | "bottom"
  | "footwear"
  | "outerwear"
  | "accessory"
  | "bag";

export type SlotState = "empty" | "filled" | "active" | "locked" | "disabled";

export type BuilderState =
  | "empty"
  | "loading"
  | "editing"
  | "saving"
  | "saved"
  | "unsaved_changes"
  | "preview"
  | "error"
  | "unavailable";

export type OutfitSource = "manual" | "ai_generated" | "editorial" | "community";

export interface OutfitItemContract {
  slot_id: string;
  product_id: string;
  title: string;
  brand: string;
  image_uri: string;
  price: number;
  original_price?: number | null;
  selected_variants?: Record<string, string>;
  is_available: boolean;
  quantity: number;
}

export interface OutfitSlotContract {
  id: string;
  category: SlotCategory;
  name: string;
  position: number;
  required: boolean;
  item?: OutfitItemContract | null;
  state: SlotState;
}

export interface OutfitContract {
  id: string;
  name: string;
  style_id: string;
  style_name: string;
  slots: OutfitSlotContract[];
  hero_image_uri?: string | null;
  source: OutfitSource;
  total_price: number;
  is_complete: boolean;
  notes?: string | null;
}

export interface CandidateItemContract {
  slot_id: string;
  category: SlotCategory;
  products: OutfitItemContract[];
}

export interface MixMatchContract {
  outfit_id: string;
  current_items: OutfitItemContract[];
  candidates_by_slot: CandidateItemContract[];
}

export interface StylePreferenceContract {
  user_id: string;
  preferred_styles: string[];
  preferred_fits: string[];
  preferred_colors: string[];
  preferred_materials: string[];
  budget_tier: string;
}

export interface SavedLookContract {
  id: string;
  user_id: string;
  name: string;
  style_name: string;
  created_at: string;
  updated_at: string;
  items: OutfitItemContract[];
  hero_image_uri?: string | null;
  is_favorite: boolean;
  collection_tag?: string | null;
}

export interface AddSlotItemRequestContract {
  slot_id: string;
  product_id: string;
  selected_variants?: Record<string, string>;
}

export interface ReplaceSlotItemRequestContract {
  slot_id: string;
  new_product_id: string;
  selected_variants?: Record<string, string>;
}

export interface SaveOutfitRequestContract {
  outfit_id: string;
  name: string;
  user_id?: string;
  collection_tag?: string | null;
}

export interface ShopOutfitAvailabilityContract {
  outfit_id: string;
  total_items: number;
  available_items: number;
  available_product_ids: string[];
  unavailable_product_ids: string[];
  can_proceed_to_cart: boolean;
  total_price: number;
}

export interface StyleHomeTemplateSpecContract {
  screen_id: StylingScreenId;
  featured_style: VisualContentModel;
  popular_styles: VisualContentModel[];
  recommended_looks: VisualContentModel[];
  saved_looks_preview: SavedLookContract[];
}

export interface OutfitBuilderTemplateSpecContract {
  screen_id: StylingScreenId;
  outfit: OutfitContract;
  active_slot_id?: string | null;
  available_categories: SlotCategory[];
  state: BuilderState;
}

export interface LookBuilderTemplateSpecContract {
  screen_id: StylingScreenId;
  look_id: string;
  title: string;
  style_tags: string[];
  context_narrative: string;
  visual_items: OutfitItemContract[];
  state: BuilderState;
}

export interface MixMatchTemplateSpecContract {
  screen_id: StylingScreenId;
  matrix: MixMatchContract;
}

export interface StyleRecommendationTemplateSpecContract {
  screen_id: StylingScreenId;
  recommended_style_name: string;
  explanation: string;
  recommended_looks: VisualContentModel[];
  recommended_products: VisualContentModel[];
}

export interface OutfitPreviewTemplateSpecContract {
  screen_id: StylingScreenId;
  outfit: OutfitContract;
  item_count: number;
  total_price: number;
}

export interface OutfitDetailTemplateSpecContract {
  screen_id: StylingScreenId;
  outfit: OutfitContract;
  constituent_items: OutfitItemContract[];
  similar_outfits: OutfitContract[];
  availability: ShopOutfitAvailabilityContract;
}

export interface SavedLooksTemplateSpecContract {
  screen_id: StylingScreenId;
  saved_looks: SavedLookContract[];
  total_saved: number;
  active_filter: string;
}

export interface StylePreferencesTemplateSpecContract {
  screen_id: StylingScreenId;
  preferences: StylePreferenceContract;
  available_styles: string[];
  available_fits: string[];
  available_colors: string[];
  available_materials: string[];
}
