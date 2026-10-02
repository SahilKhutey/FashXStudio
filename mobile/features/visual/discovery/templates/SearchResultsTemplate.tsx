/**
 * SearchResultsTemplate Component — Phase 08 (Section 8.21 - 8.24, 8.26).
 *
 * S03 - S07, S10 Multi-content search results screen:
 * - Query input bar
 * - Multi-type tabs (All, Products, Looks, Brands, Styles, Trends)
 * - Result count header
 * - Responsive 2-column grid
 * - Empty state with retry suggestions (S10)
 */

import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { SearchResultsTemplateSpec, SearchResultType } from "../types";
import { SearchInputBar } from "../SearchInputBar";
import { SearchResultTabs } from "../SearchResultTabs";
import { EmptyState } from "../../components/EmptyState";
import { ProductCard } from "../fashion/product/ProductCard";
import { LookCard } from "../fashion/look/LookCard";
import { BrandCard } from "../fashion/brand/BrandCard";
import { TrendCard } from "../fashion/trend/TrendCard";
import { VisualContentModel } from "../fashion/types";

export interface SearchResultsTemplateProps {
  spec: SearchResultsTemplateSpec;
  onChangeQuery: (text: string) => void;
  onSubmitQuery: (text: string) => void;
  onSelectTab: (tab: SearchResultType) => void;
  onItemPress: (item: VisualContentModel) => void;
  onClearFilters: () => void;
}

export const SearchResultsTemplate: React.FC<SearchResultsTemplateProps> = ({
  spec,
  onChangeQuery,
  onSubmitQuery,
  onSelectTab,
  onItemPress,
  onClearFilters,
}) => {
  const { query, activeTab, counts, items, isEmpty, emptySuggestions } = spec;

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      {/* Search Input */}
      <SearchInputBar
        query={query}
        onChangeQuery={onChangeQuery}
        onSubmitQuery={onSubmitQuery}
      />

      {/* Result Type Tabs */}
      <SearchResultTabs
        activeTab={activeTab}
        counts={counts}
        onSelectTab={onSelectTab}
      />

      {/* Result Count Summary */}
      <View style={styles.summaryRow}>
        <Text style={styles.summaryText}>
          {counts[activeTab === "all" ? "all" : activeTab]} results found for{" "}
          <Text style={styles.queryHighlight}>"{query}"</Text>
        </Text>
      </View>

      {/* Empty State (S10) */}
      {isEmpty ? (
        <View style={styles.emptyContainer}>
          <EmptyState
            title={`No results found for "${query}"`}
            description={
              emptySuggestions.length > 0
                ? emptySuggestions.join(" · ")
                : "Try searching with broader keywords or removing active filters."
            }
            actionLabel="Clear Filters"
            onAction={onClearFilters}
          />
        </View>
      ) : (
        /* Results Grid */
        <View style={styles.grid}>
          {items.map((item) => (
            <View key={item.id} style={styles.gridItem}>
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
                    curatorName: item.subtitle || "Curator",
                  }}
                  onPress={() => onItemPress(item)}
                  onSaveToggle={() => {}}
                />
              ) : item.content_type === "brand" ? (
                <BrandCard
                  brand={{
                    id: item.id,
                    name: item.title,
                    logoUri: item.media_uri,
                    category: item.category_label,
                    productCount: 24,
                    isVerified: true,
                  }}
                  onPress={() => onItemPress(item)}
                />
              ) : item.content_type === "trend" ? (
                <TrendCard
                  trend={{
                    id: item.id,
                    title: item.title,
                    category: item.category_label,
                    imageUri: item.media_uri,
                    momentum: "emerging",
                    regions: item.labels,
                  }}
                  onPress={() => onItemPress(item)}
                />
              ) : (
                <ProductCard
                  product={{
                    id: item.id,
                    brand: item.subtitle || "Brand",
                    title: item.title,
                    primaryImageUri: item.media_uri,
                    price: item.price || { amount: 2499.0 },
                    rating: item.rating,
                    category: item.category_label,
                    isSaved: item.is_saved,
                    badge: item.labels[0],
                  }}
                  onPress={() => onItemPress(item)}
                  onWishlistToggle={() => {}}
                />
              )}
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    gap: 16,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
  },
  summaryRow: {
    paddingVertical: 4,
  },
  summaryText: {
    fontSize: 14,
    color: defaultDesignTokens.neutral.neutral600,
  },
  queryHighlight: {
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
  },
  emptyContainer: {
    paddingVertical: 40,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: 12,
  },
  gridItem: {
    width: "48%",
  },
});
