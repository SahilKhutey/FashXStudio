import React from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
  FlatList,
} from "react-native";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { useUserWardrobe, UserWardrobeItem } from "../../src/features/wardrobe/hooks";

export default function ClosetScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { data: wardrobeItems, isLoading, isError, refetch, isRefetching } = useUserWardrobe();

  const renderItem = ({ item }: { item: UserWardrobeItem }) => {
    return (
      <TouchableOpacity
        style={styles.card}
        activeOpacity={0.8}
        onPress={() => router.push(`/garment/${item.garment_id}`)}
        accessibilityRole="button"
        accessibilityLabel={`Wardrobe item ${item.garment_id}`}
      >
        <View style={styles.thumbnailContainer}>
          {item.snapshot_image_key ? (
            <Image
              source={{ uri: item.snapshot_image_key }}
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
          <Text style={styles.itemTitle} numberOfLines={1}>
            {item.snapshot_title || "Saved Garment"}
          </Text>
          <Text style={styles.subText} numberOfLines={1}>
            ID: {item.garment_id.slice(0, 8)}...
          </Text>
          {item.tryon_artifact_id && (
            <View style={styles.renderedBadge}>
              <Text style={styles.renderedBadgeText}>✨ Try-On Saved</Text>
            </View>
          )}
        </View>
        <Text style={styles.chevron}>›</Text>
      </TouchableOpacity>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#4F46E5" />
      </View>
    );
  }

  if (isError) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorTitle}>{t("common.error")}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
          <Text style={styles.retryButtonText}>{t("common.retry")}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={wardrobeItems || []}
        renderItem={renderItem}
        keyExtractor={(item) => item.item_id || item.garment_id}
        refreshing={isRefetching}
        onRefresh={refetch}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>👗</Text>
            <Text style={styles.emptyTitle}>Your closet is empty</Text>
            <Text style={styles.emptySub}>
              Save garments or try-on renders from your feed to build your collection.
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  listContent: {
    padding: 16,
    flexGrow: 1,
  },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 12,
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  thumbnailContainer: {
    width: 68,
    height: 80,
    borderRadius: 8,
    backgroundColor: "#F3F4F6",
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
    fontSize: 15,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 2,
  },
  subText: {
    fontSize: 12,
    color: "#9CA3AF",
    marginBottom: 4,
  },
  renderedBadge: {
    backgroundColor: "#EEF2FF",
    alignSelf: "flex-start",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  renderedBadgeText: {
    color: "#4F46E5",
    fontSize: 11,
    fontWeight: "600",
  },
  chevron: {
    fontSize: 22,
    color: "#D1D5DB",
    paddingHorizontal: 8,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingTop: 80,
    paddingHorizontal: 24,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 8,
  },
  emptySub: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
    lineHeight: 20,
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 12,
  },
  retryButton: {
    backgroundColor: "#4F46E5",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  retryButtonText: {
    color: "#FFFFFF",
    fontWeight: "600",
  },
});
