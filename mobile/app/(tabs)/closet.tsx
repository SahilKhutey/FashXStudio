import React from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  FlatList,
} from "react-native";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { useUserWardrobe, useRemoveFromWardrobe, UserWardrobeItem } from "../../src/features/wardrobe/hooks";
import { useDesignTokens, AppText, spacing, radius } from "../../src/design-system";
import { LoadingState, ErrorState, EmptyState } from "../../src/components/states";

export default function ClosetScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { colors } = useDesignTokens();
  const { data: wardrobeItems, isLoading, isError, refetch, isRefetching } = useUserWardrobe();
  const { mutate: removeItem } = useRemoveFromWardrobe();

  const renderItem = ({ item }: { item: UserWardrobeItem }) => {
    const imageUri = item.image_url || item.snapshot_image_key;

    return (
      <TouchableOpacity
        style={[styles.card, { backgroundColor: colors.surface }]}
        activeOpacity={0.8}
        onPress={() => router.push(`/garment/${item.garment_id}`)}
        accessibilityRole="button"
        accessibilityLabel={`Wardrobe item ${item.garment_id}`}
      >
        <View style={[styles.thumbnailContainer, { backgroundColor: colors.surfaceSecondary }]}>
          {imageUri ? (
            <Image
              source={{ uri: imageUri }}
              style={styles.thumbnail}
              contentFit="cover"
            />
          ) : (
            <View style={styles.placeholderContainer}>
              <Text style={styles.placeholderIcon}>👗</Text>
            </View>
          )}
        </View>

        <View style={styles.detailsContainer}>
          <AppText variant="body" color="textPrimary" style={styles.itemTitle} numberOfLines={1}>
            {item.snapshot_title || "Saved Garment"}
          </AppText>
          <AppText variant="caption" color="textMuted" style={styles.subText} numberOfLines={1}>
            ID: {item.garment_id.slice(0, 8)}...
          </AppText>
          {item.tryon_artifact_id && (
            <View style={[styles.renderedBadge, { backgroundColor: colors.brandSubtle }]}>
              <Text style={[styles.renderedBadgeText, { color: colors.brand }]}>
                ✨ Try-On Saved
              </Text>
            </View>
          )}
        </View>
        <TouchableOpacity
          style={styles.removeButton}
          onPress={(e) => {
            e.stopPropagation();
            removeItem(item.item_id);
          }}
          accessibilityRole="button"
          accessibilityLabel="Remove from closet"
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
        >
          <Text style={[styles.removeIcon, { color: colors.textMuted }]}>✕</Text>
        </TouchableOpacity>
        <Text style={[styles.chevron, { color: colors.borderStrong }]}>›</Text>
      </TouchableOpacity>
    );
  };

  if (isLoading) {
    return <LoadingState message={t("common.loading")} />;
  }

  if (isError) {
    return <ErrorState onRetry={() => void refetch()} />;
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FlatList
        data={wardrobeItems || []}
        renderItem={renderItem}
        keyExtractor={(item) => item.item_id || item.garment_id}
        refreshing={isRefetching}
        onRefresh={() => void refetch()}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <EmptyState
            icon="👗"
            title="Your closet is empty"
            message="Save garments or try-on renders from your feed to build your collection."
            actionLabel={t("common.retry")}
            onAction={() => void refetch()}
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
  listContent: {
    padding: spacing[4],
    flexGrow: 1,
  },
  card: {
    borderRadius: radius.lg,
    padding: spacing[3],
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing[3],
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  thumbnailContainer: {
    width: 68,
    height: 80,
    borderRadius: radius.md,
    overflow: "hidden",
  },
  thumbnail: {
    width: "100%",
    height: "100%",
  },
  placeholderContainer: {
    width: "100%",
    height: "100%",
    justifyContent: "center",
    alignItems: "center",
  },
  placeholderIcon: {
    fontSize: 24,
  },
  detailsContainer: {
    flex: 1,
    marginLeft: 14,
    justifyContent: "center",
  },
  itemTitle: {
    marginBottom: 2,
  },
  subText: {
    marginBottom: 4,
  },
  renderedBadge: {
    alignSelf: "flex-start",
    paddingHorizontal: spacing[2],
    paddingVertical: 2,
    borderRadius: radius.sm,
  },
  renderedBadgeText: {
    fontSize: 11,
    fontWeight: "600",
  },
  removeButton: {
    padding: spacing[2],
    justifyContent: "center",
    alignItems: "center",
  },
  removeIcon: {
    fontSize: 14,
    fontWeight: "bold",
  },
  chevron: {
    fontSize: 22,
    paddingHorizontal: spacing[2],
  },
});
