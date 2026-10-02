/**
 * DiscoveryHomeTemplate Component — Phase 08 (Section 8.5 & 8.47 - 8.49).
 *
 * Full-screen Discovery Home layout assembling:
 * - Search bar entry trigger
 * - Hero Visual Gateway
 * - Explore category pill buttons
 * - Dynamic Discovery Rails (Editorial, Trending, Recommended, Regional Trends, Brands)
 */

import React from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { DiscoveryHomeTemplateSpec } from "../types";
import { DiscoveryHero } from "../DiscoveryHero";
import { DiscoveryRail } from "../DiscoveryRail";
import { SearchInputBar } from "../SearchInputBar";
import { VisualContentModel } from "../../fashion/types";

export interface DiscoveryHomeTemplateProps {
  spec: DiscoveryHomeTemplateSpec;
  onSearchPress: () => void;
  onExploreChipPress: (route: string) => void;
  onModuleItemPress: (item: VisualContentModel) => void;
}

export const DiscoveryHomeTemplate: React.FC<DiscoveryHomeTemplateProps> = ({
  spec,
  onSearchPress,
  onExploreChipPress,
  onModuleItemPress,
}) => {
  const { hero, exploreChips, modules, searchPlaceholder } = spec;

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      {/* Search Entry Gateway */}
      <TouchableOpacity activeOpacity={0.9} onPress={onSearchPress}>
        <View pointerEvents="none">
          <SearchInputBar
            query=""
            placeholder={searchPlaceholder}
            onChangeQuery={() => {}}
          />
        </View>
      </TouchableOpacity>

      {/* Hero Visual Banner */}
      <DiscoveryHero
        hero={hero}
        onPrimaryAction={(route) => onExploreChipPress(route)}
        onSecondaryAction={(route) => onExploreChipPress(route)}
      />

      {/* Explore Category Shortcut Chips */}
      <View style={styles.exploreSection}>
        <Text style={styles.exploreTitle}>Explore Fashion</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.chipsRow}
        >
          {exploreChips.map((chip) => (
            <TouchableOpacity
              key={chip.id}
              accessibilityLabel={`Explore ${chip.label}`}
              style={styles.chipButton}
              onPress={() => onExploreChipPress(chip.route)}
            >
              <Text style={styles.chipText}>{chip.label}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Dynamic Discovery Modules (Rails) */}
      {modules.map((mod) => (
        <DiscoveryRail
          key={mod.id}
          title={mod.title}
          description={mod.description}
          items={mod.items}
          actionLabel={mod.action?.label}
          onActionPress={() => mod.action && onExploreChipPress(mod.action.route)}
          onItemPress={onModuleItemPress}
        />
      ))}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    gap: 20,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
  },
  exploreSection: {
    gap: 8,
  },
  exploreTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
    textTransform: "uppercase",
    letterSpacing: 0.4,
  },
  chipsRow: {
    flexDirection: "row",
    gap: 8,
    paddingVertical: 4,
  },
  chipButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: defaultDesignTokens.neutral.neutral100,
    borderWidth: 1,
    borderColor: defaultDesignTokens.neutral.neutral200,
  },
  chipText: {
    fontSize: 13,
    fontWeight: "600",
    color: defaultDesignTokens.neutral.neutral800,
  },
});
