/**
 * FashXStudio Regional Maps & Geography UI System TypeScript Interfaces — Phase 11.
 *
 * Mirrors schemas/visual/geography.py Pydantic v2 data contracts.
 */

import { VisualContentModel } from "../types";

export type RegionalScreenId =
  | "M01"
  | "M02"
  | "M03"
  | "M04"
  | "M05"
  | "M06"
  | "M07"
  | "M08"
  | "M09"
  | "M10";

export type RegionType = "continent" | "country" | "state" | "city" | "local_area";

export type MarkerCategory =
  | "region"
  | "event"
  | "trend"
  | "store"
  | "collection"
  | "featured_location";

export type GeographyLayerType = "regions" | "trends" | "collections" | "products";

export type GeographyState =
  | "ready"
  | "loading"
  | "partial"
  | "empty"
  | "error"
  | "unavailable";

export interface RegionBreadcrumbContract {
  id: string;
  name: string;
  type: RegionType;
  is_current: boolean;
}

export interface RegionContract {
  id: string;
  name: string;
  type: RegionType;
  parent_id?: string | null;
  country_code?: string | null;
  state_code?: string | null;
  city_code?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  bounding_box?: number[] | null;
  timezone?: string | null;
  hero_image_uri?: string | null;
  description?: string | null;
  trends_count: number;
  looks_count: number;
  products_count: number;
  collections_count: number;
  is_supported: boolean;
}

export interface MapMarkerContract {
  id: string;
  region_id: string;
  title: string;
  category: MarkerCategory;
  latitude: number;
  longitude: number;
  is_selected: boolean;
  accent_color?: string | null;
  item_count: number;
}

export interface MapClusterContract {
  cluster_id: string;
  count: number;
  latitude: number;
  longitude: number;
  region_ids: string[];
}

export interface MapViewportContract {
  center_latitude: number;
  center_longitude: number;
  zoom_level: number;
  bounding_box?: number[] | null;
}

export interface MapViewModelContract {
  viewport: MapViewportContract;
  markers: MapMarkerContract[];
  clusters: MapClusterContract[];
  active_layers: GeographyLayerType[];
  selected_region_id?: string | null;
  state: GeographyState;
}

export interface RegionalTrendContract {
  id: string;
  region_id: string;
  region_name: string;
  title: string;
  context_narrative: string;
  momentum: string;
  media_uri: string;
  related_product_ids: string[];
  related_look_ids: string[];
}

export interface RegionalComparisonMetricContract {
  name: string;
  values_by_region: Record<string, string>;
}

export interface RegionalComparisonContract {
  region_ids: string[];
  regions: RegionContract[];
  metrics: RegionalComparisonMetricContract[];
}

export interface RegionalContentCardContract {
  id: string;
  content_type: string;
  title: string;
  subtitle?: string | null;
  media_uri: string;
  region_name: string;
  region_id: string;
}

export interface RegionalHomeTemplateSpecContract {
  screen_id: RegionalScreenId;
  featured_region: RegionContract;
  popular_regions: RegionContract[];
  featured_map: MapViewModelContract;
  regional_trends: RegionalTrendContract[];
  regional_looks: VisualContentModel[];
  local_products: VisualContentModel[];
  regional_collections: VisualContentModel[];
}

export interface FashionMapTemplateSpecContract {
  screen_id: RegionalScreenId;
  map_view: MapViewModelContract;
  selected_region?: RegionContract | null;
  available_layers: GeographyLayerType[];
  supported_regions: RegionContract[];
}

export interface RegionalExplorerTemplateSpecContract {
  screen_id: RegionalScreenId;
  breadcrumbs: RegionBreadcrumbContract[];
  regions: RegionContract[];
  active_search_query: string;
  parent_region?: RegionContract | null;
}

export interface CountryTemplateSpecContract {
  screen_id: RegionalScreenId;
  country: RegionContract;
  breadcrumbs: RegionBreadcrumbContract[];
  states_or_provinces: RegionContract[];
  regional_trends: RegionalTrendContract[];
  popular_styles: VisualContentModel[];
  local_products: VisualContentModel[];
  curated_looks: VisualContentModel[];
}

export interface StateTemplateSpecContract {
  screen_id: RegionalScreenId;
  state_region: RegionContract;
  country_region: RegionContract;
  breadcrumbs: RegionBreadcrumbContract[];
  cities: RegionContract[];
  regional_trends: RegionalTrendContract[];
  local_products: VisualContentModel[];
  curated_looks: VisualContentModel[];
}

export interface CityTemplateSpecContract {
  screen_id: RegionalScreenId;
  city: RegionContract;
  breadcrumbs: RegionBreadcrumbContract[];
  local_areas: RegionContract[];
  fashion_trends: RegionalTrendContract[];
  local_products: VisualContentModel[];
  local_looks: VisualContentModel[];
  related_cities: RegionContract[];
}

export interface RegionalTrendsTemplateSpecContract {
  screen_id: RegionalScreenId;
  region: RegionContract;
  trends: RegionalTrendContract[];
}

export interface LocalProductsTemplateSpecContract {
  screen_id: RegionalScreenId;
  region: RegionContract;
  products: VisualContentModel[];
  total_count: number;
  available_filters: string[];
}

export interface RegionalCollectionsTemplateSpecContract {
  screen_id: RegionalScreenId;
  region: RegionContract;
  featured_collection: VisualContentModel;
  collections: VisualContentModel[];
}

export interface LocationDetailTemplateSpecContract {
  screen_id: RegionalScreenId;
  location: RegionContract;
  breadcrumbs: RegionBreadcrumbContract[];
  map_view: MapViewModelContract;
  trends: RegionalTrendContract[];
  products: VisualContentModel[];
  looks: VisualContentModel[];
}
