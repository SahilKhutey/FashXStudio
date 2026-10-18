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
        <View style={styles.card}>
          <TouchableOpacity
            activeOpacity={0.9}
            onPress={() => router.push(`/garment/${item.garment_id}`)}
            accessibilityRole="button"
            accessibilityLabel={`${item.brand} ${item.title}`}
          >
            <View style={styles.imageContainer}>
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
                  <Text style={styles.tryonBadgeText}>✨ {t("feed.tryonBadge")}</Text>
                </View>
              )}
            </View>

            <View style={styles.cardContent}>
              <Text style={styles.brandText} numberOfLines={1}>
                {item.brand.toUpperCase()}
              </Text>
              <Text style={styles.titleText} numberOfLines={2}>
                {item.title}
              </Text>

              <View style={styles.priceRow}>
                <Text style={styles.priceText}>{formatPrice(item.price_minor)}</Text>
                {formattedDate ? (
                  <Text style={styles.priceFreshnessText}>
                    {t("feed.asOf", { date: formattedDate })}
                  </Text>
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

          <View style={styles.actionRow}>
            <TouchableOpacity
              style={styles.actionButtonSecondary}
              onPress={() => sendSignal(item.garment_id, "not_interested", 5000)}
              accessibilityRole="button"
              accessibilityLabel={t("feed.notInterested")}
            >
              <Text style={styles.actionSecondaryText}>{t("feed.notInterested")}</Text>
            </TouchableOpacity>

            <View style={styles.rightActions}>
              <TouchableOpacity
                style={styles.iconButton}
                onPress={() => sendSignal(item.garment_id, "like", 0)}
                accessibilityRole="button"
                accessibilityLabel={t("feed.like")}
              >
                <Text style={styles.iconText}>❤️</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.actionButtonPrimary}
                onPress={() => saveToWardrobe({ garmentId: item.garment_id })}
                disabled={isSaving}
                accessibilityRole="button"
                accessibilityLabel={t("feed.save")}
              >
                <Text style={styles.actionPrimaryText}>{t("feed.save")}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      );
    },
    [router, t, sendSignal, saveToWardrobe, isSaving]
  );

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#4F46E5" />
        <Text style={styles.loadingText}>{t("common.loading")}</Text>
      </View>
    );
  }

  if (isError) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorTitle}>{t("common.error")}</Text>
        <Text style={styles.errorSubtitle}>{t("common.networkError")}</Text>
        <TouchableOpacity
          style={styles.retryButton}
          onPress={() => refetch()}
          accessibilityRole="button"
          accessibilityLabel={t("common.retry")}
        >
          <Text style={styles.retryButtonText}>{t("common.retry")}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {relaxedFilters.length > 0 && (
        <View style={styles.relaxedBanner}>
          <Text style={styles.relaxedBannerText}>💡 {t("feed.relaxedBanner")}</Text>
        </View>
      )}

      {feedItems.length === 0 ? (
        <View style={styles.centerContainer}>
          <Text style={styles.emptyTitle}>
            {emptyReason || t("feed.empty")}
          </Text>
          <Text style={styles.emptySubtitle}>{t("feed.emptySub")}</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={() => refetch()}
            accessibilityRole="button"
          >
            <Text style={styles.retryButtonText}>{t("common.retry")}</Text>
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
                <ActivityIndicator size="small" color="#4F46E5" />
                <Text style={styles.footerLoaderText}>{t("feed.loadingMore")}</Text>
              </View>
            ) : null
          }
          contentContainerStyle={styles.listContent}
        />
      )}

      {/* 5-second Undo Snackbar */}
      {pendingSignal && (
        <View style={styles.snackbar}>
          <Text style={styles.snackbarText}>{t("feed.dismissed")}</Text>
          <TouchableOpacity
            style={styles.undoButton}
            onPress={undoSignal}
            accessibilityRole="button"
            accessibilityLabel={t("feed.undo")}
          >
            <Text style={styles.undoButtonText}>{t("feed.undo")}</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F3F4F6",
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  listContent: {
    padding: 16,
    paddingBottom: 80,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 15,
    color: "#6B7280",
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 6,
  },
  errorSubtitle: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: "#4F46E5",
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
    textAlign: "center",
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
    marginBottom: 16,
  },
  relaxedBanner: {
    backgroundColor: "#EEF2FF",
    borderBottomWidth: 1,
    borderBottomColor: "#C7D2FE",
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  relaxedBannerText: {
    fontSize: 13,
    color: "#3730A3",
    fontWeight: "500",
    lineHeight: 18,
  },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    marginBottom: 20,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 3,
  },
  imageContainer: {
    width: "100%",
    height: 380,
    backgroundColor: "#E5E7EB",
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
    borderRadius: 20,
  },
  tryonBadgeText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "600",
  },
  cardContent: {
    padding: 16,
  },
  brandText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#6B7280",
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  titleText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
    lineHeight: 22,
    marginBottom: 8,
  },
  priceRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 8,
    marginBottom: 10,
  },
  priceText: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
  },
  priceFreshnessText: {
    fontSize: 12,
    color: "#9CA3AF",
  },
  reasonsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    marginTop: 4,
  },
  actionRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingBottom: 16,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#F3F4F6",
  },
  actionButtonSecondary: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: "#F3F4F6",
  },
  actionSecondaryText: {
    fontSize: 13,
    color: "#4B5563",
    fontWeight: "500",
  },
  rightActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  iconButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: "#F3F4F6",
    justifyContent: "center",
    alignItems: "center",
  },
  iconText: {
    fontSize: 16,
  },
  actionButtonPrimary: {
    backgroundColor: "#4F46E5",
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  actionPrimaryText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#FFFFFF",
  },
  footerLoader: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: 16,
    gap: 8,
  },
  footerLoaderText: {
    fontSize: 13,
    color: "#6B7280",
  },
  snackbar: {
    position: "absolute",
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: "#1F2937",
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 6,
  },
  snackbarText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "500",
  },
  undoButton: {
    backgroundColor: "#374151",
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
  },
  undoButtonText: {
    color: "#60A5FA",
    fontSize: 14,
    fontWeight: "700",
  },
});
