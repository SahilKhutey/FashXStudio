import React, { useMemo, useState } from "react";
import {
  FlatList,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useRouter } from "expo-router";
import { useDebouncedValue } from "../../src/hooks/useDebouncedValue";
import { useProductSearch } from "../../src/features/search/search.queries";
import {
  clearSearchFilters,
  defaultSearchFilters,
  updateSearchSort,
} from "../../src/features/search/search.filters";
import { flattenSearchPages } from "../../src/features/catalog/flatten-pages";
import type {
  ProductSearchItem,
  SearchFilters,
  SearchSortOption,
} from "../../src/features/catalog/catalog.types";
import { priceToMinorUnits } from "../../src/features/catalog/utils/product-links";
import { useSaveToWardrobe } from "../../src/features/wardrobe/hooks";
import {
  useDesignTokens,
  ProductCard,
  SearchBar,
  CategoryChip,
  ProductSkeleton,
  spacing,
} from "../../src/design-system";
import { EmptyState, ErrorState } from "../../src/components/states";

const SORT_OPTIONS: { id: SearchSortOption; label: string }[] = [
  { id: "relevance", label: "Relevance" },
  { id: "price_low", label: "Price: Low" },
  { id: "price_high", label: "Price: High" },
  { id: "newest", label: "Newest" },
];

export default function ExploreScreen() {
  const router = useRouter();
  const { colors } = useDesignTokens();
  const [filters, setFilters] = useState<SearchFilters>(defaultSearchFilters);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [savingId, setSavingId] = useState<string | null>(null);

  const debouncedQuery = useDebouncedValue(filters.query, 350);
  const activeFilters = useMemo<SearchFilters>(
    () => ({ ...filters, query: debouncedQuery }),
    [filters, debouncedQuery],
  );

  const {
    data,
    isLoading,
    isError,
    refetch,
    isRefetching,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useProductSearch(activeFilters);

  const saveMutation = useSaveToWardrobe();

  const items: ProductSearchItem[] = useMemo(
    () => flattenSearchPages(data?.pages ?? []),
    [data],
  );

  const handleSave = async (item: ProductSearchItem) => {
    if (savedIds.has(item.product_id) || savingId === item.product_id) return;
    setSavingId(item.product_id);
    try {
      await saveMutation.mutateAsync({
        garmentId: item.product_id,
      });
      setSavedIds((prev) => new Set(prev).add(item.product_id));
    } finally {
      setSavingId(null);
    }
  };

  const renderProduct = ({ item }: { item: ProductSearchItem }) => {
    const isSaved = savedIds.has(item.product_id);
    const isSaving = savingId === item.product_id;

    return (
      <View style={styles.cardWrapper}>
        <ProductCard
          id={item.product_id}
          title={item.title}
          brand={item.brand.name}
          imageUrl={item.primary_image_url}
          priceMinor={priceToMinorUnits(item.price.amount)}
          currency={item.price.currency}
          tryOnSupported={false}
          saved={isSaved}
          saving={isSaving}
          onOpen={() => router.push(`/garment/${item.product_id}` as never)}
          onSave={() => {
            void handleSave(item);
          }}
        />
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.searchHeader}>
          <SearchBar
            value={filters.query}
            onChangeText={(query) =>
              setFilters((cur) => ({ ...cur, query, cursor: undefined }))
            }
            placeholder="Search styles, brands, garments..."
          />
        </View>
        <View style={styles.skeletonGrid}>
          <View style={styles.cardWrapper}>
            <ProductSkeleton />
          </View>
          <View style={styles.cardWrapper}>
            <ProductSkeleton />
          </View>
        </View>
      </View>
    );
  }

  if (isError && items.length === 0) {
    return <ErrorState onRetry={() => void refetch()} />;
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={styles.searchHeader}>
        <SearchBar
          value={filters.query}
          onChangeText={(query) =>
            setFilters((cur) => ({ ...cur, query, cursor: undefined }))
          }
          placeholder="Search styles, brands, garments..."
          onClear={() =>
            setFilters((cur) => ({ ...cur, query: "", cursor: undefined }))
          }
        />
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoryScroll}
        >
          {SORT_OPTIONS.map((opt) => (
            <CategoryChip
              key={opt.id}
              label={opt.label}
              selected={filters.sort === opt.id}
              onPress={() => setFilters((cur) => updateSearchSort(cur, opt.id))}
              style={styles.chip}
            />
          ))}
          <CategoryChip
            label="In Stock"
            selected={filters.inStock === true}
            onPress={() =>
              setFilters((cur) => ({
                ...cur,
                inStock: cur.inStock ? undefined : true,
                cursor: undefined,
              }))
            }
            style={styles.chip}
          />
        </ScrollView>
      </View>

      <FlatList
        data={items}
        renderItem={renderProduct}
        keyExtractor={(item) => `${item.product_id}:${item.merchant_product_id}`}
        numColumns={2}
        contentContainerStyle={styles.gridContent}
        columnWrapperStyle={styles.columnWrapper}
        onEndReached={() => {
          if (hasNextPage && !isFetchingNextPage) {
            void fetchNextPage();
          }
        }}
        onEndReachedThreshold={0.5}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={() => void refetch()}
            tintColor={colors.brand}
          />
        }
        ListFooterComponent={
          isFetchingNextPage ? (
            <Text style={styles.footerText}>Loading more products...</Text>
          ) : null
        }
        ListEmptyComponent={
          <EmptyState
            icon="⌕"
            title="No matching styles"
            message={
              filters.query
                ? `No products found matching "${filters.query}". Try a different keyword or clear filters.`
                : "No products match your current filters."
            }
            actionLabel="Clear Filters"
            onAction={() => setFilters((cur) => clearSearchFilters(cur))}
          />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  searchHeader: {
    paddingHorizontal: spacing[4],
    paddingTop: spacing[3],
    paddingBottom: spacing[2],
  },
  categoryScroll: {
    paddingVertical: spacing[2],
    gap: spacing[2],
  },
  chip: {
    marginRight: spacing[2],
  },
  gridContent: {
    padding: spacing[3],
    flexGrow: 1,
  },
  columnWrapper: {
    gap: spacing[3],
    marginBottom: spacing[3],
  },
  cardWrapper: {
    flex: 1,
  },
  skeletonGrid: {
    flexDirection: "row",
    padding: spacing[3],
    gap: spacing[3],
  },
  footerText: {
    textAlign: "center",
    paddingVertical: spacing[3],
    color: "#6B7280",
    fontSize: 12,
  },
});
