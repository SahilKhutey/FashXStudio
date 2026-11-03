import React, { useCallback, useMemo, useRef, useState } from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
} from "react-native";
import { FlashList, type ViewToken } from "@shopify/flash-list";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import {
  useFeed,
  useSignal,
  useImpressionTracker,
  FeedItem,
} from "../../src/features/feed/hooks";
import { useSaveToWardrobe } from "../../src/features/wardrobe/hooks";
import {
  useDesignTokens,
  AppText,
  ProductCard,
  SearchBar,
  CategoryChip,
  SectionHeader,
  ProductSkeleton,
  spacing,
  radius,
} from "../../src/design-system";
import {
  LoadingState,
  ErrorState,
  EmptyState,
} from "../../src/components/states";

const FEED_CATEGORIES = [
  { id: "all", label: "For You" },
  { id: "top", label: "Tops" },
  { id: "bottom", label: "Bottoms" },
  { id: "one_piece", label: "Dresses & Sets" },
  { id: "outerwear", label: "Outerwear" },
];

export default function FeedScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { colors } = useDesignTokens();

  const [activeCategory, setActiveCategory] = useState("all");
  const [savedGarmentIds, setSavedGarmentIds] = useState<Set<string>>(new Set());
  const [savingGarmentId, setSavingGarmentId] = useState<string | null>(null);

  const {
    data,
    isLoading,
    isError,
    refetch,
    isRefetching,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useFeed();

  const { sendSignal, pendingSignal } = useSignal();
  const { recordImpression } = useImpressionTracker();
  const { mutateAsync: saveToWardrobe } = useSaveToWardrobe();

  // Combine items from all pages, excluding the one currently pending dismissal
  const feedItems = useMemo(() => {
    if (!data?.pages) return [];
    const all = data.pages.flatMap((page) => page.items || []);
    const filtered = pendingSignal
      ? all.filter((item) => item.garment_id !== pendingSignal.garmentId)
      : all;

    if (activeCategory === "all") return filtered;
    return filtered.filter(
      (item) => item.category?.toLowerCase() === activeCategory.toLowerCase()
    );
  }, [data?.pages, pendingSignal, activeCategory]);

  const relaxedFilters = useMemo(() => {
    if (!data?.pages || data.pages.length === 0) return [];
    return data.pages[0]?.relaxed || [];
  }, [data?.pages]);

  const emptyReason = useMemo(() => {
    if (!data?.pages || data.pages.length === 0) return null;
    return data.pages[0]?.empty_reason || null;
  }, [data?.pages]);

  // Viewable items tracker for impression analytics
  const onViewableItemsChanged = useRef(
    ({ viewableItems }: { viewableItems: ViewToken<FeedItem>[] }) => {
      viewableItems.forEach((viewItem) => {
        const garmentId = viewItem.item?.garment_id;
        if (viewItem.isViewable && garmentId) {
          recordImpression(garmentId);
        }
      });
    }
  ).current;

  const handleSave = async (item: FeedItem) => {
    const garmentId = item.garment_id;
    if (savedGarmentIds.has(garmentId) || savingGarmentId === garmentId) return;

    setSavingGarmentId(garmentId);
    try {
      await saveToWardrobe({
        garmentId,
      });
      setSavedGarmentIds((prev) => new Set(prev).add(garmentId));
    } finally {
      setSavingGarmentId(null);
    }
  };

  const renderFeedCard = useCallback(
    ({ item }: { item: FeedItem }) => {
      const garmentId = item.garment_id;
      const isSaved = savedGarmentIds.has(garmentId);
      const isSaving = savingGarmentId === garmentId;

      return (
        <View style={styles.cardContainer}>
          <ProductCard
            id={garmentId}
            title={item.title}
            brand={item.brand}
            imageUrl={item.image_url}
            priceMinor={item.price_minor}
            currency="INR"
            tryOnSupported={item.tryon_supported ?? true}
            saved={isSaved}
            saving={isSaving}
            onOpen={() => router.push(`/garment/${garmentId}` as any)}
            onSave={() => handleSave(item)}
            onTryOn={() => router.push(`/garment/${garmentId}` as any)}
          />

          {/* Quick stylist taste feedback */}
          <View style={[styles.feedbackBar, { backgroundColor: colors.surfaceSecondary }]}>
            {item.stylist_explanation ? (
              <AppText variant="caption" color="textSecondary" numberOfLines={1} style={styles.explanationText}>
                ✦ {item.stylist_explanation}
              </AppText>
            ) : (
              <AppText variant="caption" color="textMuted">
                Curated for your style profile
              </AppText>
            )}

            <View style={styles.signalButtons}>
              <TouchableOpacity
                onPress={() => sendSignal(garmentId, "not_interested", 5000)}
                accessibilityRole="button"
                accessibilityLabel="Not interested"
                style={styles.signalButton}
              >
                <Text style={styles.signalIcon}>✕</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => sendSignal(garmentId, "like", 0)}
                accessibilityRole="button"
                accessibilityLabel="Like look"
                style={styles.signalButton}
              >
                <Text style={styles.signalIcon}>♥</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      );
    },
    [router, colors, savedGarmentIds, savingGarmentId, sendSignal]
  );

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.headerArea}>
          <SectionHeader title="Discover" subtitle="Curated daily fashion edits" />
        </View>
        <View style={styles.skeletonContainer}>
          <ProductSkeleton />
        </View>
      </View>
    );
  }

  if (isError) {
    return <ErrorState onRetry={() => void refetch()} />;
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header Search Shortcut & Category Chips */}
      <View style={styles.headerArea}>
        <TouchableOpacity
          activeOpacity={0.8}
          onPress={() => router.push("/explore" as any)}
          accessibilityRole="button"
          accessibilityLabel="Search catalog"
        >
          <SearchBar
            value=""
            onChangeText={() => {}}
            onSubmit={() => router.push("/explore" as any)}
            placeholder="Search styles, brands, garments..."
            style={styles.searchShortcut}
          />
        </TouchableOpacity>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoryScroll}
        >
          {FEED_CATEGORIES.map((cat) => (
            <CategoryChip
              key={cat.id}
              label={cat.label}
              selected={activeCategory === cat.id}
              onPress={() => setActiveCategory(cat.id)}
              style={styles.chip}
            />
          ))}
        </ScrollView>
      </View>

      {relaxedFilters.length > 0 && (
        <View
          style={[
            styles.relaxedBanner,
            { backgroundColor: colors.brandSubtle, borderBottomColor: colors.border },
          ]}
        >
          <AppText variant="caption" color="textSecondary">
            💡 {t("feed.relaxedBanner")}
          </AppText>
        </View>
      )}

      {feedItems.length === 0 ? (
        <EmptyState
          icon="✦"
          title={
            emptyReason === "catalog_empty"
              ? "New styles are arriving soon"
              : "Let's refresh your style preferences"
          }
          message={
            emptyReason === "catalog_empty"
              ? "We couldn't find eligible products in the current catalog."
              : "Try exploring other categories or adjusting your preferences."
          }
          actionLabel="Explore styles"
          onAction={() => router.push("/explore" as any)}
        />
      ) : (
        <FlashList
          data={feedItems}
          renderItem={renderFeedCard}
          keyExtractor={(item) => item.garment_id}
          onEndReached={() => {
            if (hasNextPage && !isFetchingNextPage) {
              void fetchNextPage();
            }
          }}
          onEndReachedThreshold={0.5}
          onViewableItemsChanged={onViewableItemsChanged}
          refreshing={isRefetching}
          onRefresh={() => void refetch()}
          ListFooterComponent={
            isFetchingNextPage ? (
              <LoadingState message={t("feed.loadingMore")} compact />
            ) : null
          }
          contentContainerStyle={styles.listContent}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  headerArea: {
    paddingHorizontal: spacing[4],
    paddingTop: spacing[3],
    paddingBottom: spacing[2],
  },
  searchShortcut: {
    pointerEvents: "none",
  },
  categoryScroll: {
    paddingVertical: spacing[2],
    gap: spacing[2],
  },
  chip: {
    marginRight: spacing[2],
  },
  relaxedBanner: {
    paddingHorizontal: spacing[4],
    paddingVertical: spacing[2],
    borderBottomWidth: 1,
  },
  listContent: {
    paddingHorizontal: spacing[4],
    paddingBottom: spacing[6],
  },
  cardContainer: {
    marginBottom: spacing[4],
  },
  feedbackBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing[3],
    paddingVertical: spacing[2],
    borderRadius: radius.md,
    marginTop: spacing[2],
  },
  explanationText: {
    flex: 1,
    marginRight: spacing[2],
  },
  signalButtons: {
    flexDirection: "row",
    gap: spacing[2],
  },
  signalButton: {
    padding: spacing[1],
  },
  signalIcon: {
    fontSize: 16,
    color: "#6B7280",
  },
  skeletonContainer: {
    padding: spacing[4],
  },
});
