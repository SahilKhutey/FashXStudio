/**
 * SearchResultTabs Component — Phase 08 (Section 8.22 & 8.23).
 *
 * Content-type tab navigation for broad search queries:
 * All (124) | Products (74) | Looks (20) | Brands (12) | Styles (10) | Trends (8)
 */

import React from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { SearchResultCounts, SearchResultType } from "./types";

export interface SearchResultTabsProps {
  activeTab: SearchResultType;
  counts: SearchResultCounts;
  onSelectTab: (tab: SearchResultType) => void;
}

interface TabConfig {
  key: SearchResultType;
  label: string;
  countKey: keyof SearchResultCounts;
}

const TABS: TabConfig[] = [
  { key: "all", label: "All", countKey: "all" },
  { key: "products", label: "Products", countKey: "products" },
  { key: "looks", label: "Looks", countKey: "looks" },
  { key: "brands", label: "Brands", countKey: "brands" },
  { key: "styles", label: "Styles", countKey: "styles" },
  { key: "trends", label: "Trends", countKey: "trends" },
];

export const SearchResultTabs: React.FC<SearchResultTabsProps> = ({
  activeTab,
  counts,
  onSelectTab,
}) => {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.container}
    >
      {TABS.map((tab) => {
        const isSelected = activeTab === tab.key;
        const count = counts[tab.countKey];

        return (
          <TouchableOpacity
            key={tab.key}
            accessibilityLabel={`View ${tab.label} results (${count})`}
            onPress={() => onSelectTab(tab.key)}
            style={[styles.tabButton, isSelected && styles.tabButtonSelected]}
          >
            <Text style={[styles.tabLabel, isSelected && styles.tabLabelSelected]}>
              {tab.label}
            </Text>
            {count > 0 ? (
              <View style={[styles.countBadge, isSelected && styles.countBadgeSelected]}>
                <Text style={[styles.countText, isSelected && styles.countTextSelected]}>
                  {count}
                </Text>
              </View>
            ) : null}
          </TouchableOpacity>
        );
      })}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    gap: 8,
    paddingVertical: 8,
  },
  tabButton: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: defaultDesignTokens.neutral.neutral100,
    borderWidth: 1,
    borderColor: defaultDesignTokens.neutral.neutral200,
    gap: 6,
  },
  tabButtonSelected: {
    backgroundColor: defaultDesignTokens.brand.primary,
    borderColor: defaultDesignTokens.brand.primary,
  },
  tabLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: defaultDesignTokens.neutral.neutral700,
  },
  tabLabelSelected: {
    color: defaultDesignTokens.surfaces.surfaceLight,
  },
  countBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    backgroundColor: defaultDesignTokens.neutral.neutral200,
  },
  countBadgeSelected: {
    backgroundColor: "rgba(255, 255, 255, 0.25)",
  },
  countText: {
    fontSize: 11,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral700,
  },
  countTextSelected: {
    color: defaultDesignTokens.surfaces.surfaceLight,
  },
});
