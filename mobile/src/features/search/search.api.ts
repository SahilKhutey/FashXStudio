import { api } from "../../api/client";
import { ProductSearchResponseSchema } from "../catalog/catalog.schema";
import type {
  ProductSearchResponse,
  SearchFacetsResponse,
  SearchFilters,
} from "../catalog/catalog.types";

export function buildSearchQueryParams(
  filters: SearchFilters,
  limit = 20,
): string {
  const params = new URLSearchParams();
  if (filters.query.trim()) {
    params.set("q", filters.query.trim());
  }
  if (filters.categoryId) {
    params.set("category_id", filters.categoryId);
  }
  if (filters.brandId) {
    params.set("brand_id", filters.brandId);
  }
  if (filters.colorId) {
    params.set("color_id", filters.colorId);
  }
  if (filters.size) {
    params.set("size", filters.size);
  }
  if (filters.minPrice !== undefined) {
    params.set("min_price", String(filters.minPrice));
  }
  if (filters.maxPrice !== undefined) {
    params.set("max_price", String(filters.maxPrice));
  }
  if (filters.currency) {
    params.set("currency", filters.currency);
  }
  if (filters.inStock !== undefined) {
    params.set("in_stock", String(filters.inStock));
  }
  params.set("sort", filters.sort);
  params.set("limit", String(limit));
  if (filters.cursor) {
    params.set("cursor", filters.cursor);
  }
  return params.toString();
}

export async function searchProducts(
  filters: SearchFilters,
  signal?: AbortSignal,
): Promise<ProductSearchResponse> {
  const qs = buildSearchQueryParams(filters, 20);
  const raw = await api<unknown>(`/search/products?${qs}`, { signal });
  return ProductSearchResponseSchema.parse(raw);
}

export async function getSearchFacets(
  filters: Pick<SearchFilters, "query" | "categoryId">,
): Promise<SearchFacetsResponse> {
  const params = new URLSearchParams();
  if (filters.query.trim()) {
    params.set("q", filters.query.trim());
  }
  if (filters.categoryId) {
    params.set("category_id", filters.categoryId);
  }
  const qs = params.toString();
  return api<SearchFacetsResponse>(`/search/facets${qs ? `?${qs}` : ""}`);
}
