import React, { useState } from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  Alert,
} from "react-native";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import {
  useUserWardrobe,
  useRemoveFromWardrobe,
  UserWardrobeItem,
} from "../../src/features/wardrobe/hooks";
import {
  useDesignTokens,
  AppText,
  SectionHeader,
  spacing,
  radius,
} from "../../src/design-system";
import { LoadingState, ErrorState, EmptyState } from "../../src/components/states";

export default function ClosetScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { colors } = useDesignTokens();
  const {
    data: wardrobeItems,
    isLoading,
    isError,
    refetch,
    isRefetching,
  } = useUserWardrobe();
  const { mutate: removeItem } = useRemoveFromWardrobe();
  const [removingId, setRemovingId] = useState<string | null>(null);

  const confirmRemove = (itemId: string, title?: string) => {
    Alert.alert(
      "Remove from Closet",
      `Are you sure you want to remove ${title || "this item"} from your closet?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Remove",
          style: "destructive",
          onPress: () => {
            if (removingId) return;
            setRemovingId(itemId);
            removeItem(itemId, {
              onSettled: () => setRemovingId(null),
            });
          },
        },
      ]
    );
  };

  const renderItem = ({ item }: { item: UserWardrobeItem }) => {
    const imageUri =
      item.image_url ||
      (item.snapshot_image_key?.startsWith("http://") ||
      item.snapshot_image_key?.startsWith("https://")
        ? item.snapshot_image_key
        : undefined);

    const formattedPrice =
      item.snapshot_price_minor && item.snapshot_price_minor > 0
        ? new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: item.snapshot_currency || "INR",
            maximumFractionDigits: 0,
          }).format(item.snapshot_price_minor / 100)
        : null;

    return (
      <TouchableOpacity
        style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}
        activeOpacity={0.8}
        onPress={() => router.push(`/garment/${item.garment_id}` as any)}
        accessibilityRole="button"
        accessibilityLabel={`Wardrobe item ${item.snapshot_title || item.garment_id}`}
      >
        <View
          style={[
            styles.thumbnailContainer,
            { backgroundColor: colors.surfaceSecondary },
          ]}
        >
          {imageUri ? (
            <Image
              source={{ uri: imageUri }}
              style={styles.thumbnail}
              contentFit="cover"
              transition={200}
            />
          ) : (
            <View style={styles.placeholderContainer}>
              <Text style={styles.placeholderIcon}>👗</Text>
            </View>
          )}
        </View>

        <View style={styles.detailsContainer}>
          <AppText
            variant="body"
            color="textPrimary"
            style={styles.itemTitle}
            numberOfLines={1}
          >
            {item.snapshot_title || "Saved Garment"}
          </AppText>

          {formattedPrice && (
            <AppText
              variant="label"
              color="textPrimary"
              style={styles.priceText}
            >
              {formattedPrice}
            </AppText>
          )}

          <View style={styles.badgesRow}>
            {item.tryon_artifact_id ? (
              <View
                style={[
                  styles.badge,
                  { backgroundColor: colors.brandSubtle },
                ]}
              >
                <AppText variant="caption" color="textPrimary">
                  ✦ Look Saved
                </AppText>
              </View>
            ) : null}
          </View>
        </View>

        <TouchableOpacity
          style={styles.removeButton}
          disabled={removingId === item.item_id}
          onPress={() => confirmRemove(item.item_id, item.snapshot_title)}
          accessibilityRole="button"
          accessibilityLabel="Remove from closet"
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
        >
          {removingId === item.item_id ? (
            <ActivityIndicator size="small" color={colors.textMuted} />
          ) : (
            <Text style={[styles.removeIcon, { color: colors.textMuted }]}>
              ✕
            </Text>
          )}
        </TouchableOpacity>
      </TouchableOpacity>
    );
  };

  if (isLoading) {
    return <LoadingState message={t("common.loading")} />;
  }

  if (isError) {
    return <ErrorState onRetry={() => void refetch()} />;
  }

  const count = wardrobeItems?.length || 0;

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FlatList
        data={wardrobeItems || []}
        renderItem={renderItem}
        keyExtractor={(item) => item.item_id || item.garment_id}
        refreshing={isRefetching}
        onRefresh={() => void refetch()}
        contentContainerStyle={styles.listContent}
        ListHeaderComponent={
          count > 0 ? (
            <SectionHeader
              title="My Closet"
              subtitle={`${count} ${count === 1 ? "style" : "styles"} saved`}
              actionLabel="Add more"
              onAction={() => router.push("/explore" as any)}
            />
          ) : undefined
        }
        ListEmptyComponent={
          <EmptyState
            icon="♧"
            title="Your closet is empty"
            message="Save garments and virtual try-on looks from your feed to build your collection."
            actionLabel="Explore styles"
            onAction={() => router.push("/explore" as any)}
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
    marginBottom: spacing[3],
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
  },
  thumbnailContainer: {
    width: 72,
    height: 96,
    borderRadius: radius.md,
    overflow: "hidden",
  },
  thumbnail: {
    width: "100%",
    height: "100%",
  },
  placeholderContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  placeholderIcon: {
    fontSize: 28,
  },
  detailsContainer: {
    flex: 1,
    marginLeft: spacing[3],
    justifyContent: "center",
  },
  itemTitle: {
    fontWeight: "600",
    marginBottom: 4,
  },
  priceText: {
    marginBottom: 4,
  },
  badgesRow: {
    flexDirection: "row",
    gap: 6,
    marginTop: 2,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  removeButton: {
    padding: 8,
    justifyContent: "center",
    alignItems: "center",
  },
  removeIcon: {
    fontSize: 16,
  },
});
