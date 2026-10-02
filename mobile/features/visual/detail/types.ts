/**
 * Product & Fashion Detail Screens TypeScript Interfaces — Phase 09.
 *
 * Mirrors schemas/visual/detail.py Pydantic v2 data contracts.
 */

import { VisualContentModel } from "../types";

export type DetailScreenId =
  | "P01"
  | "P02"
  | "P03"
  | "P04"
  | "P05"
  | "P06"
  | "P07"
  | "P08"
  | "P09"
  | "P10"
  | "F01"
  | "F02"
  | "F03"
  | "F04"
  | "F05"
  | "F06"
  | "F07"
  | "F08"
  | "F09";

export type ProductAvailabilityState =
  | "in_stock"
  | "low_stock"
  | "out_of_stock"
  | "pre_order"
  | "unavailable"
  | "unknown";

export type MediaType =
  | "image"
  | "thumbnail"
  | "detail"
  | "lifestyle"
  | "model"
  | "video"
  | "view_360";

export type VariantOptionState = "available" | "selected" | "unavailable" | "loading";

export type RelatedItemRelationship =
  | "similar"
  | "recommended"
  | "styled_with"
  | "recently_viewed"
  | "trending";

export type DetailState =
  | "loading"
  | "ready"
  | "partial"
  | "empty"
  | "error"
  | "not_found"
  | "unavailable";

export interface BreadcrumbItemContract {
  label: string;
  route: string;
  is_current?: boolean;
}

export interface MediaItemContract {
  id: string;
  uri: string;
  media_type?: MediaType;
  alt_text: string;
  aspect_ratio?: string;
  is_primary?: boolean;
  order?: number;
}

export interface ProductGalleryContract {
  items: MediaItemContract[];
  active_index?: number;
  zoom_enabled?: boolean;
}

export interface VariantOptionItemContract {
  id: string;
  label: string;
  value: string;
  state?: VariantOptionState;
  swatch_hex?: string | null;
}

export interface VariantGroupContract {
  group_id: string;
  name: string;
  options: VariantOptionItemContract[];
  selected_option_id?: string | null;
}

export interface SpecificationItemContract {
  label: string;
  value: string;
}

export interface SpecificationSectionContract {
  group_name: string;
  items: SpecificationItemContract[];
}

export interface ReviewDistributionItemContract {
  stars: number;
  count: number;
  percentage: number;
}

export interface ProductReviewItemContract {
  id: string;
  author: string;
  rating: number;
  date: string;
  comment: string;
  is_verified?: boolean;
  helpful_count?: number;
}

export interface ProductReviewsContract {
  average_rating: number;
  total_reviews: number;
  distribution: ReviewDistributionItemContract[];
  reviews: ProductReviewItemContract[];
  state?: DetailState;
}

export interface RelatedProductItemContract {
  relationship: RelatedItemRelationship;
  product_id: string;
  title: string;
  brand: string;
  image_uri: string;
  price: number;
  original_price?: number | null;
  reason?: string | null;
}

export interface LookHotspotContract {
  product_id: string;
  label: string;
  x_percent: number;
  y_percent: number;
}

export interface LookItemLinkContract {
  slot: string;
  product_id: string;
  title: string;
  brand: string;
  price: number;
  image_uri: string;
}

export interface AttributeComparisonItemContract {
  attribute_name: string;
  values: Record<string, string>;
}

export interface ProductComparisonDetailContract {
  product_ids: string[];
  products: Record<string, any>[];
  attributes: AttributeComparisonItemContract[];
}

export interface ProductDetailViewModelContract {
  id: string;
  brand: string;
  title: string;
  price: number;
  original_price?: number | null;
  currency?: string;
  discount_percentage?: number | null;
  rating?: number;
  review_count?: number;
  availability?: ProductAvailabilityState;
  stock_units?: number | null;
  short_summary: string;
  description: string;
  gallery: ProductGalleryContract;
  variant_groups: VariantGroupContract[];
  specifications: SpecificationSectionContract[];
  reviews: ProductReviewsContract;
  similar_products: RelatedProductItemContract[];
  recommended_products: RelatedProductItemContract[];
  styled_with: RelatedProductItemContract[];
  breadcrumbs: BreadcrumbItemContract[];
  state?: DetailState;
}

export interface ComprehensiveProductDetailTemplateSpecContract {
  screen_id: DetailScreenId;
  view_model: ProductDetailViewModelContract;
}

export interface ProductReviewsTemplateSpecContract {
  screen_id: DetailScreenId;
  product_id: string;
  reviews: ProductReviewsContract;
}

export interface ProductAvailabilityTemplateSpecContract {
  screen_id: DetailScreenId;
  product_id: string;
  availability: ProductAvailabilityState;
  stock_units?: number | null;
  estimated_delivery_days?: number;
  postal_code_supported?: boolean;
  shipping_origin?: string;
}

export interface ProductComparisonTemplateSpecContract {
  screen_id: DetailScreenId;
  comparison: ProductComparisonDetailContract;
}

export interface FashionStoryDetailTemplateSpecContract {
  screen_id: DetailScreenId;
  id: string;
  title: string;
  subtitle: string;
  author: string;
  published_date: string;
  category: string;
  hero_media_uri: string;
  content_markdown: string;
  related_looks: VisualContentModel[];
  related_products: VisualContentModel[];
  state?: DetailState;
}

export interface FashionArticleDetailTemplateSpecContract {
  screen_id: DetailScreenId;
  id: string;
  category: string;
  title: string;
  subtitle: string;
  author: string;
  published_date: string;
  hero_media_uri: string;
  body_markdown: string;
  inline_media_uris: string[];
  related_products: VisualContentModel[];
  state?: DetailState;
}

export interface FashionCollectionDetailTemplateSpecContract {
  screen_id: DetailScreenId;
  id: string;
  name: string;
  season: string;
  description: string;
  curator: string;
  hero_image_uri: string;
  looks: VisualContentModel[];
  products: VisualContentModel[];
  styles: VisualContentModel[];
  related_collections: VisualContentModel[];
  state?: DetailState;
}

export interface FashionLookDetailTemplateSpecContract {
  screen_id: DetailScreenId;
  id: string;
  name: string;
  style: string;
  context_description: string;
  hero_image_uri: string;
  outfit_items: LookItemLinkContract[];
  hotspots: LookHotspotContract[];
  related_looks: VisualContentModel[];
  is_saved?: boolean;
  state?: DetailState;
}

export interface FashionInspirationDetailTemplateSpecContract {
  screen_id: DetailScreenId;
  id: string;
  title: string;
  context: string;
  media_uri: string;
  style_tags: string[];
  related_looks: VisualContentModel[];
  related_products: VisualContentModel[];
  is_saved?: boolean;
  state?: DetailState;
}

export interface BrandStoryDetailTemplateSpecContract {
  screen_id: DetailScreenId;
  id: string;
  brand_name: string;
  hero_image_uri: string;
  logo_uri: string;
  story_markdown: string;
  values: string[];
  collections: VisualContentModel[];
  featured_products: VisualContentModel[];
  featured_looks: VisualContentModel[];
  is_verified?: boolean;
  state?: DetailState;
}

export interface EditorialViewTemplateSpecContract {
  screen_id: DetailScreenId;
  id: string;
  title: string;
  hero_media_uri: string;
  narrative_blocks: Record<string, string>[];
  curated_looks: VisualContentModel[];
  curated_products: VisualContentModel[];
  state?: DetailState;
}
