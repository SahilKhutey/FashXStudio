/**
 * FashXStudio Mobile Discovery & Search Types — Phase 08.
 *
 * Mirrors backend Pydantic contracts from schemas.visual.discovery (Sections 8.1-8.82).
 */

import { VisualContentModel } from "../fashion/types";
import { FilterState, SortOption } from "../shopping/types";

export type DiscoveryScreenId =
  | "D01"
  | "D02"
  | "D03"
  | "D04"
  | "D05"
  | "D06"
  | "D07"
  | "D08"
  | "D09"
  | "D10"
  | "S01"
  | "S02"
  | "S03"
  | "S04"
  | "S05"
  | "S06"
  | "S07"
  | "S08"
  | "S09"
  | "S10";

export type ExploreType =
  | "fashion"
  | "products"
  | "looks"
  | "collections"
  | "brands"
  | "styles"
  | "trends";

export type SearchResultType =
  | "all"
  | "products"
  | "looks"
  | "brands"
  | "styles"
  | "trends";

export type SuggestionType =
  | "query"
  | "product"
  | "brand"
  | "style"
  | "trend"
  | "category";

export type DiscoveryModuleType =
  | "featured_collection"
  | "trending_products"
  | "popular_styles"
  | "recommended_looks"
  | "regional_trends"
  | "editorial_story"
  | "brand_showcase";

export type DiscoveryState =
  | "loading"
  | "ready"
  | "empty"
  | "partial"
  | "error"
  | "unavailable";

export interface DiscoveryHero {
  id: string;
  title: string;
  subtitle: string;
  mediaUri: string;
  primaryActionLabel: string;
  primaryActionRoute: string;
  secondaryActionLabel?: string;
  secondaryActionRoute?: string;
}

export interface DiscoveryModuleAction {
  label: string;
  route: string;
}

export interface DiscoveryModule {
  id: string;
  moduleType: DiscoveryModuleType;
  title: string;
  description?: string;
  items: VisualContentModel[];
  action?: DiscoveryModuleAction;
  priority?: number;
  visibility?: boolean;
  state?: DiscoveryState;
}

export interface DiscoveryViewModel {
  hero?: DiscoveryHero;
  modules: DiscoveryModule[];
  hasPersonalization?: boolean;
  state?: DiscoveryState;
}

export interface SearchSuggestion {
  text: string;
  suggestionType: SuggestionType;
  targetId?: string;
  count?: number;
  category?: string;
}

export interface RecentSearch {
  query: string;
  timestamp: string;
}

export interface SearchResultCounts {
  all: number;
  products: number;
  looks: number;
  brands: number;
  styles: number;
  trends: number;
}

export interface AdvancedSearchCriteria {
  keywords?: string;
  category?: string;
  brand?: string;
  style?: string;
  priceMin?: number;
  priceMax?: number;
  color?: string;
  size?: string;
  region?: string;
}

export interface SearchViewModel {
  query: string;
  resultType: SearchResultType;
  counts: SearchResultCounts;
  results: VisualContentModel[];
  suggestions: SearchSuggestion[];
  recentSearches: RecentSearch[];
  filterState?: FilterState;
  sort: SortOption;
  state: DiscoveryState;
}

// --- Templates ---

export interface DiscoveryHomeTemplateSpec {
  screenId: DiscoveryScreenId;
  searchPlaceholder: string;
  hero: DiscoveryHero;
  exploreChips: Array<{ id: string; label: string; route: string }>;
  modules: DiscoveryModule[];
}

export interface ExploreTemplateSpec {
  screenId: DiscoveryScreenId;
  exploreType: ExploreType;
  title: string;
  description: string;
  featuredItems: VisualContentModel[];
  gridItems: VisualContentModel[];
  totalCount: number;
}

export interface PersonalizedDiscoveryTemplateSpec {
  screenId: DiscoveryScreenId;
  userId: string;
  userStyleTags: string[];
  modules: DiscoveryModule[];
  recommendationExplanations: Record<string, string>;
}

export interface DiscoveryResultsTemplateSpec {
  screenId: DiscoveryScreenId;
  query: string;
  resultsByType: Record<string, VisualContentModel[]>;
  totalCount: number;
}

export interface SearchHomeTemplateSpec {
  screenId: DiscoveryScreenId;
  recentSearches: RecentSearch[];
  trendingSearches: string[];
  exploreCategories: Array<{ id: string; label: string; query: string }>;
}

export interface SearchResultsTemplateSpec {
  screenId: DiscoveryScreenId;
  query: string;
  activeTab: SearchResultType;
  counts: SearchResultCounts;
  items: VisualContentModel[];
  filterState?: FilterState;
  sort: SortOption;
  isEmpty: boolean;
  emptySuggestions: string[];
}

export interface AdvancedSearchTemplateSpec {
  screenId: DiscoveryScreenId;
  criteria: AdvancedSearchCriteria;
  previewResults: VisualContentModel[];
  previewTotal: number;
}
