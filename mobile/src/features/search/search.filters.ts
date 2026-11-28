import type { SearchFilters, SearchSortOption } from "../catalog/catalog.types";

export const defaultSearchFilters: SearchFilters = {
  query: "",
  currency: "INR",
  sort: "relevance",
};

export function updateSearchSort(
  filters: SearchFilters,
  sort: SearchSortOption,
): SearchFilters {
  return {
    ...filters,
    sort,
    cursor: undefined,
  };
}

export function clearSearchFilters(filters: SearchFilters): SearchFilters {
  return {
    query: filters.query,
    currency: filters.currency,
    sort: filters.sort,
    cursor: undefined,
  };
}

export function validatePriceRange(
  minPrice?: number,
  maxPrice?: number,
): boolean {
  if (minPrice !== undefined && (!Number.isFinite(minPrice) || minPrice < 0)) {
    return false;
  }
  if (maxPrice !== undefined && (!Number.isFinite(maxPrice) || maxPrice < 0)) {
    return false;
  }
  if (minPrice !== undefined && maxPrice !== undefined && minPrice > maxPrice) {
    return false;
  }
  return true;
}
