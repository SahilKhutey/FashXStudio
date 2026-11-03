import React, { useMemo, useState } from "react";
import {
  FlatList,
  RefreshControl,
  ScrollView,
  StyleSheet,
  View,
} from "react-native";
import { useRouter } from "expo-router";
import { useFeed, FeedItem } from "../../src/features/feed/hooks";
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

const CATEGORIES = [
  { id: "all", label: "All Styles" },
  { id: "top", label: "Tops" },
  { id: "bottom", label: "Bottoms" },
  { id: "one_piece", label: "Dresses & Sets" },
  { id: "footwear", label: "Shoes" },
  { id: "accessory", label: "Accessories" },
];

export default function ExploreScreen() {
  const router = useRouter();
  const { colors } = useDesignTokens();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [savingId, setSavingId] = useState<string | null>(null);

  const {
    data,
    isLoading,
    isError,
    refetch,
    isRefetching,
  } = useFeed();

  const saveMutation = useSaveToWardrobe();

  // Flatten items from all feed pages
  const allItems: FeedItem[] = useMemo(() => {
    if (!data?.pages) return [];
    const set = new Map<string, FeedItem>();
    for (const page of data.pages) {
      for (const item of page.items || []) {
        if (!set.has(item.garment_id)) {
          set.set(item.garment_id, item);
        }
      }
    }
    return Array.from(set.values());
  }, [data]);

  // Client-side filtering by search query and category
  const filteredItems = useMemo(() => {
    return allItems.filter((item) => {
      const matchesCategory =
        selectedCategory === "all" ||
        item.category?.toLowerCase() === selectedCategory.toLowerCase();

      const query = searchQuery.trim().toLowerCase();
      const matchesSearch =
        !query ||
        item.title?.toLowerCase().includes(query) ||
        item.brand?.toLowerCase().includes(query) ||
        item.category?.toLowerCase().includes(query);

      return matchesCategory && matchesSearch;
    });
  }, [allItems, selectedCategory, searchQuery]);

  const handleSave = async (item: FeedItem) => {
    if (savedIds.has(item.garment_id) || savingId === item.garment_id) return;
    setSavingId(item.garment_id);
    try {
      await saveMutation.mutateAsync({
        garmentId: item.garment_id,
      });
      setSavedIds((prev) => new Set(prev).add(item.garment_id));
    } finally {
      setSavingId(null);
    }
  };

  const renderProduct = ({ item }: { item: FeedItem }) => {
    const isSaved = savedIds.has(item.garment_id);
    const isSaving = savingId === item.garment_id;

    return (
      <View style={styles.cardWrapper}>
        <ProductCard
          id={item.garment_id}
          title={item.title}
          brand={item.brand}
          imageUrl={item.image_url}
          priceMinor={item.price_minor}
          currency="INR"
          tryOnSupported={item.tryon_supported ?? true}
          saved={isSaved}
          saving={isSaving}
          onOpen={() => router.push(`/garment/${item.garment_id}` as any)}
          onSave={() => handleSave(item)}
          onTryOn={() => router.push(`/garment/${item.garment_id}` as any)}
        />
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.searchHeader}>
          <SearchBar
            value={searchQuery}
            onChangeText={setSearchQuery}
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

  if (isError) {
    return <ErrorState onRetry={() => void refetch()} />;
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={styles.searchHeader}>
        <SearchBar
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholder="Search styles, brands, garments..."
          onClear={() => setSearchQuery("")}
        />
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoryScroll}
        >
          {CATEGORIES.map((cat) => (
            <CategoryChip
              key={cat.id}
              label={cat.label}
              selected={selectedCategory === cat.id}
              onPress={() => setSelectedCategory(cat.id)}
              style={styles.chip}
            />
          ))}
        </ScrollView>
      </View>

      <FlatList
        data={filteredItems}
        renderItem={renderProduct}
        keyExtractor={(item) => item.garment_id}
        numColumns={2}
        contentContainerStyle={styles.gridContent}
        columnWrapperStyle={styles.columnWrapper}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={() => void refetch()}
            tintColor={colors.brand}
          />
        }
        ListEmptyComponent={
          <EmptyState
            icon="⌕"
            title="No matching styles"
            message={
              searchQuery
                ? `No styles found matching "${searchQuery}". Try a different keyword or category.`
                : "No products available in this category."
            }
            actionLabel="Clear Filters"
            onAction={() => {
              setSearchQuery("");
              setSelectedCategory("all");
            }}
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
});
