/**
 * RecentSearchesList Component — Phase 08 (Section 8.20).
 *
 * Renders recent search history pills with individual removal
 * and batch clear all triggers.
 */

import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { RecentSearch } from "./types";

export interface RecentSearchesListProps {
  searches: RecentSearch[];
  onSelectSearch: (query: string) => void;
  onRemoveSearch?: (query: string) => void;
  onClearAll?: () => void;
}

export const RecentSearchesList: React.FC<RecentSearchesListProps> = ({
  searches,
  onSelectSearch,
  onRemoveSearch,
  onClearAll,
}) => {
  if (searches.length === 0) {
    return null;
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Recent Searches</Text>
        {onClearAll ? (
          <TouchableOpacity onPress={onClearAll}>
            <Text style={styles.clearAllText}>Clear All</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      <View style={styles.pillsRow}>
        {searches.map((item, index) => (
          <View key={`${item.query}-${index}`} style={styles.pill}>
            <TouchableOpacity
              onPress={() => onSelectSearch(item.query)}
              style={styles.pillQuery}
            >
              <Text style={styles.queryText}>{item.query}</Text>
            </TouchableOpacity>

            {onRemoveSearch ? (
              <TouchableOpacity
                accessibilityLabel={`Remove ${item.query} from recent searches`}
                onPress={() => onRemoveSearch(item.query)}
                style={styles.removeIcon}
              >
                <Text style={styles.removeText}>✕</Text>
              </TouchableOpacity>
            ) : null}
          </View>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    gap: 10,
    marginVertical: 12,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: {
    fontSize: 14,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
    textTransform: "uppercase",
    letterSpacing: 0.4,
  },
  clearAllText: {
    fontSize: 12,
    fontWeight: "600",
    color: defaultDesignTokens.brand.primary,
  },
  pillsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: defaultDesignTokens.neutral.neutral100,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: defaultDesignTokens.neutral.neutral200,
    gap: 6,
  },
  pillQuery: {
    justifyContent: "center",
  },
  queryText: {
    fontSize: 13,
    color: defaultDesignTokens.neutral.neutral800,
    fontWeight: "500",
  },
  removeIcon: {
    justifyContent: "center",
    alignItems: "center",
    paddingLeft: 2,
  },
  removeText: {
    fontSize: 11,
    color: defaultDesignTokens.neutral.neutral400,
    fontWeight: "700",
  },
});
