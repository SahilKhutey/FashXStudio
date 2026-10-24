import React, { useCallback, useMemo, useRef } from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
  ViewToken,
} from "react-native";
import { FlashList } from "@shopify/flash-list";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import {
  useFeed,
  useSignal,
  useImpressionTracker,
  FeedItem,
} from "../../src/features/feed/hooks";
import { useSaveToWardrobe } from "../../src/features/wardrobe/hooks";
import { Chip } from "../../src/components/Chip";
import {
  useDesignTokens,
  AppText,
  spacing,
  radius,
  elevation,
} from "../../src/design-system";

function formatPrice(priceMinor: number): string {
  const amount = (priceMinor / 100).toFixed(0);
  return `₹${amount}`;
}

function formatDate(isoDate?: string | null): string {
  if (!isoDate) return "";
  try {
    const d = new Date(isoDate);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

export default function FeedScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { colors } = useDesignTokens();

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

  const { sendSignal, undoSignal, pendingSignal } = useSignal();
  const { recordImpression } = useImpressionTracker();
  const { mutate: saveToWardrobe, isPending: isSaving } = useSaveToWardrobe();

  // Combine items from all pages, excluding the one currently pending dismissal
  const feedItems = useMemo(() => {
    if (!data?.pages) return [];
    const all = data.pages.flatMap((page) => page.items || []);
    if (!pendingSignal) return all;
    return all.filter((item) => item.garment_id !== pendingSignal.garmentId);
  }, [data?.pages, pendingSignal]);

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
    ({ viewableItems }: { viewableItems: ViewToken[] }) => {
      viewableItems.forEach((viewItem) => {
        if (viewItem.isViewable && viewItem.item?.garment_id) {
          recordImpression(viewItem.item.garment_id);
        }
      });
    }
  ).current;

  const renderFeedCard = useCallback(
    ({ item }: { item: FeedItem }) => {
      const stableCacheKey = item.image_url ? item.image_url.split("?")[0] : undefined;
      const formattedDate = formatDate(item.price_updated_at);

      return (
        <View style={[styles.card, { backgroundColor: colors.surface }]}>
          <TouchableOpacity
            activeOpacity={0.9}
            onPress={() => router.push(`/garment/${item.garment_id}`)}
            accessibilityRole="button"
            accessibilityLabel={`${item.brand} ${item.title}`}
          >
            <View style={[styles.imageContainer, { backgroundColor: colors.surfaceSecondary }]}>
              {item.image_url ? (
                <Image
                  source={{ uri: item.image_url, cacheKey: stableCacheKey }}
                  style={styles.garmentImage}
                  contentFit="cover"
                  transition={200}
                />
              ) : (
                <View style={styles.placeholderImage}>
                  <Text style={styles.placeholderText}>👗</Text>
                </View>
              )}

              {item.tryon_supported && (
                <View style={styles.tryonBadge}>
                  <AppText variant="caption" color="textOnBrand" style={styles.tryonBadgeText}>
                    ✨ {t("feed.tryonBadge")}
                  </AppText>
                </View>
              )}
            </View>

            <View style={styles.cardContent}>
              <AppText
                variant="label"
                color="textMuted"
                style={styles.brandText}
                numberOfLines={1}
              >
                {item.brand.toUpperCase()}
              </AppText>
              <AppText
                variant="body"
                color="textPrimary"
                style={styles.titleText}
                numberOfLines={2}
              >
                {item.title}
              </AppText>

              <View style={styles.priceRow}>
                <AppText variant="heading3" color="textPrimary" style={styles.priceText}>
                  {formatPrice(item.price_minor)}
                </AppText>
                {formattedDate ? (
                  <AppText variant="caption" color="textMuted" style={styles.priceFreshnessText}>
                    {t("feed.asOf", { date: formattedDate })}
                  </AppText>
                ) : null}
              </View>

              {item.reason_chips && item.reason_chips.length > 0 && (
                <View style={styles.reasonsContainer}>
                  {item.reason_chips.slice(0, 2).map((chip, idx) => (
                    <Chip key={idx} label={chip} selected={false} />
                  ))}
                </View>
              )}
            </View>
          </TouchableOpacity>

          <View style={[styles.actionRow, { borderTopColor: colors.border }]}>
            <TouchableOpacity
              style={[styles.actionButtonSecondary, { backgroundColor: colors.surfaceSecondary }]}
              onPress={() => sendSignal(item.garment_id, "not_interested", 5000)}
              accessibilityRole="button"
              accessibilityLabel={t("feed.notInterested")}
            >
              <AppText variant="label" color="textSecondary" style={styles.actionSecondaryText}>
                {t("feed.notInterested")}
              </AppText>
            </TouchableOpacity>

            <View style={styles.rightActions}>
              <TouchableOpacity
                style={[styles.iconButton, { backgroundColor: colors.surfaceSecondary }]}
                onPress={() => sendSignal(item.garment_id, "like", 0)}
                accessibilityRole="button"
                accessibilityLabel={t("feed.like")}
              >
                <Text style={styles.iconText}>❤️</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButtonPrimary, { backgroundColor: colors.brand }]}
                onPress={() => saveToWardrobe({ garmentId: item.garment_id })}
                disabled={isSaving}
                accessibilityRole="button"
                accessibilityLabel={t("feed.save")}
              >
                <AppText variant="label" color="textOnBrand" style={styles.actionPrimaryText}>
                  {t("feed.save")}
                </AppText>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      );
    },
    [router, t, sendSignal, saveToWardrobe, isSaving, colors]
  );

  if (isLoading) {
    return (
      <View style={[styles.centerContainer, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.brand} />
        <AppText variant="body" color="textMuted" style={styles.loadingText}>
          {t("common.loading")}
        </AppText>
      </View>
    );
  }

  if (isError) {
    return (
      <View style={[styles.centerContainer, { backgroundColor: colors.background }]}>
        <AppText variant="heading2" color="textPrimary" style={styles.errorTitle}>
          {t("common.error")}
        </AppText>
        <AppText variant="body" color="textSecondary" style={styles.errorSubtitle}>
          {t("common.networkError")}
        </AppText>
        <TouchableOpacity
          style={[styles.retryButton, { backgroundColor: colors.brand }]}
          onPress={() => refetch()}
          accessibilityRole="button"
          accessibilityLabel={t("common.retry")}
        >
          <AppText variant="label" color="textOnBrand" style={styles.retryButtonText}>
            {t("common.retry")}
          </AppText>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {relaxedFilters.length > 0 && (
        <View
          style={[
            styles.relaxedBanner,
            { backgroundColor: colors.brandSubtle, borderBottomColor: colors.border },
          ]}
        >
          <AppText variant="caption" color="textSecondary" style={styles.relaxedBannerText}>
            💡 {t("feed.relaxedBanner")}
          </AppText>
        </View>
      )}

      {feedItems.length === 0 ? (
        <View style={styles.centerContainer}>
          <AppText variant="heading2" color="textPrimary" style={styles.emptyTitle}>
            {emptyReason || t("feed.empty")}
          </AppText>
          <AppText variant="body" color="textSecondary" style={styles.emptySubtitle}>
            {t("feed.emptySub")}
          </AppText>
          <TouchableOpacity
            style={[styles.retryButton, { backgroundColor: colors.brand }]}
            onPress={() => refetch()}
            accessibilityRole="button"
          >
            <AppText variant="label" color="textOnBrand" style={styles.retryButtonText}>
              {t("common.retry")}
            </AppText>
          </TouchableOpacity>
        </View>
      ) : (
        <FlashList
          data={feedItems}
          renderItem={renderFeedCard}
          keyExtractor={(item) => item.garment_id}
          onEndReached={() => {
            if (hasNextPage && !isFetchingNextPage) {
              fetchNextPage();
            }
          }}
          onEndReachedThreshold={0.5}
          onViewableItemsChanged={onViewableItemsChanged}
          refreshing={isRefetching}
          onRefresh={refetch}
          ListFooterComponent={
            isFetchingNextPage ? (
              <View style={styles.footerLoader}>
                <ActivityIndicator size="small" color={colors.brand} />
                <AppText variant="caption" color="textMuted" style={styles.footerLoaderText}>
                  {t("feed.loadingMore")}
                </AppText>
              </View>
            ) : null
          }
          contentContainerStyle={styles.listContent}
        />
      )}

      {/* 5-second Undo Snackbar */}
      {pendingSignal && (
        <View style={styles.snackbar}>
          <AppText variant="body" color="textOnBrand" style={styles.snackbarText}>
            {t("feed.dismissed")}
          </AppText>
          <TouchableOpacity
            style={styles.undoButton}
            onPress={undoSignal}
            accessibilityRole="button"
            accessibilityLabel={t("feed.undo")}
          >
            <AppText variant="label" style={styles.undoButtonText}>
              {t("feed.undo")}
            </AppText>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: spacing[6],
  },
  listContent: {
    padding: spacing[4],
    paddingBottom: spacing[20],
  },
  loadingText: {
    marginTop: spacing[3],
  },
  errorTitle: {
    marginBottom: spacing[1.5],
  },
  errorSubtitle: {
    textAlign: "center",
    marginBottom: spacing[4],
  },
  retryButton: {
    paddingHorizontal: spacing[5],
    paddingVertical: 10,
    borderRadius: radius.md,
  },
  retryButtonText: {
    color: "#FFFFFF",
  },
  emptyTitle: {
    textAlign: "center",
    marginBottom: spacing[2],
  },
  emptySubtitle: {
    textAlign: "center",
    marginBottom: spacing[4],
  },
  relaxedBanner: {
    borderBottomWidth: 1,
    paddingHorizontal: spacing[4],
    paddingVertical: 10,
  },
  relaxedBannerText: {
    lineHeight: 18,
  },
  card: {
    borderRadius: radius.xl,
    marginBottom: spacing[5],
    overflow: "hidden",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: elevation.medium,
  },
  imageContainer: {
    width: "100%",
    height: 380,
    position: "relative",
  },
  garmentImage: {
    width: "100%",
    height: "100%",
  },
  placeholderImage: {
    width: "100%",
    height: "100%",
    justifyContent: "center",
    alignItems: "center",
  },
  placeholderText: {
    fontSize: 64,
  },
  tryonBadge: {
    position: "absolute",
    top: 14,
    left: 14,
    backgroundColor: "rgba(17, 24, 39, 0.85)",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: radius.pill,
  },
  tryonBadgeText: {
    color: "#FFFFFF",
  },
  cardContent: {
    padding: spacing[4],
  },
  brandText: {
    letterSpacing: 0.8,
    marginBottom: spacing[1],
  },
  titleText: {
    lineHeight: 22,
    marginBottom: spacing[2],
  },
  priceRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: spacing[2],
    marginBottom: 10,
  },
  priceText: {},
  priceFreshnessText: {},
  reasonsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing[1.5],
    marginTop: spacing[1],
  },
  actionRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing[4],
    paddingBottom: spacing[4],
    paddingTop: spacing[2],
    borderTopWidth: 1,
  },
  actionButtonSecondary: {
    paddingVertical: spacing[2],
    paddingHorizontal: spacing[3],
    borderRadius: radius.md,
  },
  actionSecondaryText: {},
  rightActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  iconButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    justifyContent: "center",
    alignItems: "center",
  },
  iconText: {
    fontSize: 16,
  },
  actionButtonPrimary: {
    paddingVertical: spacing[2],
    paddingHorizontal: spacing[4],
    borderRadius: radius.md,
  },
  actionPrimaryText: {
    color: "#FFFFFF",
  },
  footerLoader: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: spacing[4],
    gap: spacing[2],
  },
  footerLoaderText: {},
  snackbar: {
    position: "absolute",
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: "#1F2937",
    borderRadius: radius.lg,
    paddingVertical: spacing[3],
    paddingHorizontal: spacing[4],
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: elevation.high,
  },
  snackbarText: {
    color: "#FFFFFF",
  },
  undoButton: {
    backgroundColor: "#374151",
    paddingVertical: 6,
    paddingHorizontal: spacing[3],
    borderRadius: radius.sm,
  },
  undoButtonText: {
    color: "#60A5FA",
  },
});
