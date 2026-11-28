export type SearchSortOption =
  | "relevance"
  | "price_low"
  | "price_high"
  | "newest"
  | "recently_updated"
  | "popularity"
  | "similarity";

export type CatalogAvailability =
  | "IN_STOCK"
  | "OUT_OF_STOCK"
  | "UNKNOWN"
  | "DISCONTINUED"
  | "DELISTED"
  | "TAKEDOWN"
  | "STALE";

export type SearchBrandInfo = {
  id: string | null;
  name: string;
};

export type SearchPriceInfo = {
  amount: string | number;
  currency: string;
  original_amount?: string | number | null;
};

export type ProductSearchItem = {
  product_id: string;
  merchant_product_id: string;
  title: string;
  brand: SearchBrandInfo;
  price: SearchPriceInfo;
  availability: string;
  matched_attributes: string[];
  primary_image_url: string | null;
  similarity_score?: number | null;
};

export type ProductSearchResponse = {
  search_id: string;
  query: string | null;
  items: ProductSearchItem[];
  total: number;
  next_cursor: string | null;
  applied_filters: Record<string, unknown>;
  suggestions: string[];
  facets: Record<string, unknown>;
  sort: string;
};

export type SearchFacetsResponse = {
  facets: Record<string, Array<Record<string, unknown>>>;
};

export type SearchFilters = {
  query: string;
  categoryId?: string;
  brandId?: string;
  colorId?: string;
  size?: string;
  minPrice?: number;
  maxPrice?: number;
  currency: string;
  inStock?: boolean;
  sort: SearchSortOption;
  cursor?: string;
};
