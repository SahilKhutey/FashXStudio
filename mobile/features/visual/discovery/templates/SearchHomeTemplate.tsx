/**
 * SearchHomeTemplate Component — Phase 08 (Section 8.16).
 *
 * S01 Search Home gateway layout with:
 * - Search input bar
 * - Autocomplete suggestion list
 * - Recent search history
 * - Trending keyword tags
 * - Category navigation
 */

import React, { useState } from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { SearchHomeTemplateSpec, SearchSuggestion } from "../types";
import { SearchInputBar } from "../SearchInputBar";
import { SearchSuggestionsList } from "../SearchSuggestionsList";
import { RecentSearchesList } from "../RecentSearchesList";

export interface SearchHomeTemplateProps {
  spec: SearchHomeTemplateSpec;
  suggestions: SearchSuggestion[];
  onSearchSubmit: (query: string) => void;
  onSelectSuggestion: (suggestion: SearchSuggestion) => void;
  onClearRecentSearches?: () => void;
}

export const SearchHomeTemplate: React.FC<SearchHomeTemplateProps> = ({
  spec,
  suggestions,
  onSearchSubmit,
  onSelectSuggestion,
  onClearRecentSearches,
}) => {
  const [query, setQuery] = useState<string>("");

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      {/* Search Input Bar */}
      <SearchInputBar
        query={query}
        onChangeQuery={setQuery}
        onSubmitQuery={onSearchSubmit}
        onClearQuery={() => setQuery("")}
      />

      {/* Autocomplete Suggestions if typing */}
      {query.length > 0 ? (
        <SearchSuggestionsList
          suggestions={suggestions}
          onSelectSuggestion={onSelectSuggestion}
        />
      ) : null}

      {/* Recent Searches */}
      {spec.recentSearches.length > 0 && query.length === 0 ? (
        <RecentSearchesList
          searches={spec.recentSearches}
          onSelectSearch={onSearchSubmit}
          onClearAll={onClearRecentSearches}
        />
      ) : null}

      {/* Trending Search Keywords */}
      {query.length === 0 ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Trending Searches</Text>
          <View style={styles.trendingRow}>
            {spec.trendingSearches.map((keyword, index) => (
              <TouchableOpacity
                key={`${keyword}-${index}`}
                accessibilityLabel={`Search trending ${keyword}`}
                style={styles.trendingChip}
                onPress={() => onSearchSubmit(keyword)}
              >
                <Text style={styles.trendingText}>🔥 {keyword}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      ) : null}

      {/* Explore Categories */}
      {query.length === 0 ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Browse by Category</Text>
          <View style={styles.categoriesGrid}>
            {spec.exploreCategories.map((cat) => (
              <TouchableOpacity
                key={cat.id}
                accessibilityLabel={`Browse category ${cat.label}`}
                style={styles.categoryCard}
                onPress={() => onSearchSubmit(cat.query)}
              >
                <Text style={styles.categoryText}>{cat.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      ) : null}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    gap: 20,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
  },
  section: {
    gap: 10,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
    textTransform: "uppercase",
    letterSpacing: 0.4,
  },
  trendingRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  trendingChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    backgroundColor: defaultDesignTokens.neutral.neutral100,
    borderWidth: 1,
    borderColor: defaultDesignTokens.neutral.neutral200,
  },
  trendingText: {
    fontSize: 13,
    fontWeight: "600",
    color: defaultDesignTokens.neutral.neutral800,
  },
  categoriesGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  categoryCard: {
    width: "48%",
    padding: 16,
    borderRadius: 12,
    backgroundColor: defaultDesignTokens.neutral.neutral100,
    borderWidth: 1,
    borderColor: defaultDesignTokens.neutral.neutral200,
  },
  categoryText: {
    fontSize: 14,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
  },
});
