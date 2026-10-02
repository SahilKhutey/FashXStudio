/**
 * SearchSuggestionsList Component — Phase 08 (Section 8.18 & 8.19).
 *
 * Renders categorized autocomplete suggestions (query, product, brand, style, trend, category)
 * with type icons and selection callbacks.
 */

import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { SearchSuggestion } from "./types";
import { Badge } from "../../components/Badge";

export interface SearchSuggestionsListProps {
  suggestions: SearchSuggestion[];
  onSelectSuggestion: (suggestion: SearchSuggestion) => void;
}

export const SearchSuggestionsList: React.FC<SearchSuggestionsListProps> = ({
  suggestions,
  onSelectSuggestion,
}) => {
  if (suggestions.length === 0) {
    return null;
  }

  const getBadgeVariant = (type: string) => {
    switch (type) {
      case "brand":
        return "primary";
      case "style":
      case "trend":
        return "accent";
      case "product":
        return "secondary";
      default:
        return "neutral";
    }
  };

  return (
    <View style={styles.container}>
      {suggestions.map((suggestion, index) => (
        <TouchableOpacity
          key={`${suggestion.text}-${index}`}
          accessibilityLabel={`Search for ${suggestion.text}`}
          style={styles.suggestionRow}
          onPress={() => onSelectSuggestion(suggestion)}
        >
          <View style={styles.textContainer}>
            <Text style={styles.suggestionText}>{suggestion.text}</Text>
            {suggestion.count ? (
              <Text style={styles.countText}>({suggestion.count})</Text>
            ) : null}
          </View>

          <Badge
            label={suggestion.suggestionType.toUpperCase()}
            variant={getBadgeVariant(suggestion.suggestionType)}
            size="sm"
          />
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: defaultDesignTokens.neutral.neutral200,
    overflow: "hidden",
    marginTop: 8,
  },
  suggestionRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: defaultDesignTokens.neutral.neutral100,
  },
  textContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  suggestionText: {
    fontSize: 14,
    fontWeight: "500",
    color: defaultDesignTokens.neutral.neutral800,
  },
  countText: {
    fontSize: 12,
    color: defaultDesignTokens.neutral.neutral400,
  },
});
