/**
 * DiscoveryRail Component — Phase 08 (Section 8.37).
 *
 * Horizontal scrolling discovery rail for products, looks,
 * styles, and trends with header title, count, and view-all action.
 */

import React from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { VisualContentModel } from "../fashion/types";
import { ProductCard } from "../fashion/product/ProductCard";
import { LookCard } from "../fashion/look/LookCard";
import { CollectionCard } from "../fashion/collection/CollectionCard";

export interface DiscoveryRailProps {
  title: string;
  description?: string;
  items: VisualContentModel[];
  actionLabel?: string;
  onActionPress?: () => void;
  onItemPress?: (item: VisualContentModel) => void;
}

export const DiscoveryRail: React.FC<DiscoveryRailProps> = ({
  title,
  description,
  items,
  actionLabel,
  onActionPress,
  onItemPress,
}) => {
  return (
    <View style={styles.container}>
      {/* Rail Header */}
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Text style={styles.title}>{title}</Text>
          {description ? <Text style={styles.description}>{description}</Text> : null}
        </View>

        {actionLabel && onActionPress ? (
          <TouchableOpacity
            accessibilityLabel={`${actionLabel} for ${title}`}
            onPress={onActionPress}
            style={styles.actionButton}
          >
            <Text style={styles.actionText}>{actionLabel} →</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      {/* Horizontal Rail */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.railContent}
      >
        {items.map((item) => {
          return (
            <View key={item.id} style={styles.cardWrapper}>
              <TouchableOpacity
                activeOpacity={0.9}
                onPress={() => onItemPress?.(item)}
              >
                {item.content_type === "look" ? (
                  <LookCard
                    look={{
                      id: item.id,
                      title: item.title,
                      styleName: item.category_label,
                      heroImageUri: item.media_uri,
                      itemsCount: 3,
                      associatedProductIds: item.relationships["products"] || [],
                      isSaved: item.is_saved,
                      curatorName: item.subtitle || "FashX Editorial",
                    }}
                    onPress={() => onItemPress?.(item)}
                    onSaveToggle={() => {}}
                  />
                ) : item.content_type === "collection" ? (
                  <CollectionCard
                    collection={{
                      id: item.id,
                      title: item.title,
                      description: item.subtitle || "",
                      heroImageUri: item.media_uri,
                      itemCount: 24,
                      seasonTag: "Capsule '26",
                      isSaved: item.is_saved,
                    }}
                    onPress={() => onItemPress?.(item)}
                    onSaveToggle={() => {}}
                  />
                ) : (
                  <ProductCard
                    product={{
                      id: item.id,
                      brand: item.subtitle || "FashX",
                      title: item.title,
                      primaryImageUri: item.media_uri,
                      price: item.price || { amount: 2999.0 },
                      rating: item.rating,
                      category: item.category_label,
                      isSaved: item.is_saved,
                      badge: item.labels[0],
                    }}
                    onPress={() => onItemPress?.(item)}
                    onWishlistToggle={() => {}}
                  />
                )}
              </TouchableOpacity>
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    gap: 12,
    marginVertical: 12,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    paddingHorizontal: 16,
  },
  titleContainer: {
    flex: 1,
    gap: 2,
  },
  title: {
    fontSize: 18,
    fontWeight: "800",
    color: defaultDesignTokens.neutral.neutral900,
    letterSpacing: 0.2,
  },
  description: {
    fontSize: 12,
    color: defaultDesignTokens.neutral.neutral500,
  },
  actionButton: {
    paddingVertical: 4,
  },
  actionText: {
    fontSize: 13,
    fontWeight: "700",
    color: defaultDesignTokens.brand.primary,
  },
  railContent: {
    paddingHorizontal: 16,
    gap: 14,
  },
  cardWrapper: {
    width: 220,
  },
});
