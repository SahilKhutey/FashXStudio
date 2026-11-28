import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import type {
  ProductSearchResponse,
  SearchFacetsResponse,
  SearchFilters,
} from "../catalog/catalog.types";
import { getSearchFacets, searchProducts } from "./search.api";

export function useProductSearch(filters: SearchFilters, enabled = true) {
  return useInfiniteQuery<ProductSearchResponse, Error>({
    queryKey: ["search", "products", filters],
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam, signal }) =>
      searchProducts(
        { ...filters, cursor: pageParam as string | undefined },
        signal,
      ),
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled,
    staleTime: 30_000,
    gcTime: 5 * 60_000,
    retry: 1,
  });
}

export function useSearchFacets(
  filters: Pick<SearchFilters, "query" | "categoryId">,
  enabled = true,
) {
  return useQuery<SearchFacetsResponse, Error>({
    queryKey: ["search", "facets", filters.query, filters.categoryId],
    queryFn: () => getSearchFacets(filters),
    enabled,
    staleTime: 5 * 60_000,
    retry: 1,
  });
}
