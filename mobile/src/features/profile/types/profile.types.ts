export type SizeSystem = 'IN' | 'US' | 'UK' | 'EU' | 'INTL';

export type PreferredFit =
  | 'SLIM'
  | 'REGULAR'
  | 'RELAXED'
  | 'OVERSIZED'
  | 'NO_PREFERENCE';

export type StylePreference =
  | 'CASUAL'
  | 'FORMAL'
  | 'STREETWEAR'
  | 'BOHEMIAN'
  | 'MINIMALIST'
  | 'VINTAGE'
  | 'ATHLEISURE'
  | 'BUSINESS_CASUAL'
  | 'ETHNIC'
  | 'PARTYWEAR';

export type ColorPreference =
  | 'BLACK'
  | 'WHITE'
  | 'NAVY'
  | 'GREY'
  | 'BEIGE'
  | 'BROWN'
  | 'RED'
  | 'BLUE'
  | 'GREEN'
  | 'YELLOW'
  | 'PINK'
  | 'PURPLE'
  | 'ORANGE'
  | 'PASTELS'
  | 'EARTH_TONES'
  | 'JEWEL_TONES';

export type ProductCategory =
  | 'TOPS'
  | 'BOTTOMS'
  | 'DRESSES'
  | 'OUTERWEAR'
  | 'ACTIVEWEAR'
  | 'FORMALWEAR'
  | 'FOOTWEAR'
  | 'ACCESSORIES'
  | 'TRADITIONAL';

export type ShoppingIntent =
  | 'EVERYDAY'
  | 'WORK'
  | 'SPECIAL_OCCASION'
  | 'VACATION'
  | 'LOUNGE'
  | 'FITNESS';

export interface ShoppingBudget {
  min?: number | null;
  max?: number | null;
  currency?: string;
}

export interface ShoppingPreferences {
  budget?: ShoppingBudget;
  shopping_intents?: ShoppingIntent[];
  preferred_brands?: string[];
  avoid_materials?: string[];
  sustainability_preference?: boolean;
}

export interface CategorySizeItem {
  category_code: string;
  size_system: SizeSystem;
  size_label: string;
}

export interface ShopperProfile {
  id: string;
  user_id: string;
  height_cm?: number | null;
  weight_kg?: number | null;
  preferred_size_system?: SizeSystem | null;
  preferred_fit?: PreferredFit | null;
  style_preferences: StylePreference[];
  preferred_colors: ColorPreference[];
  product_categories: ProductCategory[];
  shopping_preferences: ShoppingPreferences;
  category_sizes: CategorySizeItem[];
  build?: string | null;
  consents?: Record<string, boolean>;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ShopperProfileCreate {
  height_cm?: number | null;
  weight_kg?: number | null;
  preferred_size_system?: SizeSystem | null;
  preferred_fit?: PreferredFit | null;
  style_preferences?: StylePreference[];
  preferred_colors?: ColorPreference[];
  product_categories?: ProductCategory[];
  shopping_preferences?: ShoppingPreferences;
  category_sizes?: CategorySizeItem[];
}

export interface ShopperProfileUpdate {
  height_cm?: number | null;
  weight_kg?: number | null;
  preferred_size_system?: SizeSystem | null;
  preferred_fit?: PreferredFit | null;
  style_preferences?: StylePreference[];
  preferred_colors?: ColorPreference[];
  product_categories?: ProductCategory[];
  shopping_preferences?: ShoppingPreferences;
  expected_version?: number;
}

export interface FeatureReadiness {
  ready: boolean;
  missing_fields: string[];
}

export interface FeatureCompleteness {
  overall_percentage: number;
  features: {
    product_discovery: FeatureReadiness;
    personalized_recommendations: FeatureReadiness;
    size_guidance: FeatureReadiness;
    fit_recommendation: FeatureReadiness;
    advanced_vto: FeatureReadiness;
  };
}
