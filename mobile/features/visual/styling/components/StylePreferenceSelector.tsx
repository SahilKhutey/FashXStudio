import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from "react-native";
import { StylePreferenceContract } from "../types";

interface StylePreferenceSelectorProps {
  preferences: StylePreferenceContract;
  availableStyles: string[];
  availableFits: string[];
  availableColors: string[];
  availableMaterials: string[];
  onToggleStyle: (style: string) => void;
  onToggleFit: (fit: string) => void;
  onToggleColor: (color: string) => void;
  onToggleMaterial: (material: string) => void;
  onChangeBudget: (tier: string) => void;
  testID?: string;
}

export const StylePreferenceSelector: React.FC<StylePreferenceSelectorProps> = ({
  preferences,
  availableStyles,
  availableFits,
  availableColors,
  availableMaterials,
  onToggleStyle,
  onToggleFit,
  onToggleColor,
  onToggleMaterial,
  onChangeBudget,
  testID = "style-preference-selector",
}) => {
  const budgetTiers = ["budget", "medium", "premium", "luxury"];

  const renderChipGroup = (
    title: string,
    items: string[],
    selectedItems: string[],
    onToggle: (item: string) => void,
    groupKey: string
  ) => {
    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>{title}</Text>
        <View style={styles.chipRow}>
          {items.map((item) => {
            const isSelected = selectedItems.includes(item);
            return (
              <TouchableOpacity
                key={`${groupKey}-${item}`}
                testID={`pref-chip-${groupKey}-${item}`}
                activeOpacity={0.8}
                onPress={() => onToggle(item)}
                style={[styles.chip, isSelected && styles.selectedChip]}
              >
                <Text style={[styles.chipText, isSelected && styles.selectedChipText]}>
                  {item}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>
    );
  };

  return (
    <ScrollView
      testID={testID}
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* Styles */}
      {renderChipGroup(
        "Aesthetic & Styles",
        availableStyles,
        preferences.preferred_styles,
        onToggleStyle,
        "style"
      )}

      {/* Fits */}
      {renderChipGroup("Preferred Fits", availableFits, preferences.preferred_fits, onToggleFit, "fit")}

      {/* Colors */}
      {renderChipGroup(
        "Color Palette",
        availableColors,
        preferences.preferred_colors,
        onToggleColor,
        "color"
      )}

      {/* Materials */}
      {renderChipGroup(
        "Fabrics & Materials",
        availableMaterials,
        preferences.preferred_materials,
        onToggleMaterial,
        "mat"
      )}

      {/* Budget Tier */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Budget Preference</Text>
        <View style={styles.chipRow}>
          {budgetTiers.map((tier) => {
            const isSelected = preferences.budget_tier === tier;
            return (
              <TouchableOpacity
                key={`budget-${tier}`}
                testID={`pref-budget-${tier}`}
                activeOpacity={0.8}
                onPress={() => onChangeBudget(tier)}
                style={[styles.chip, isSelected && styles.selectedChip]}
              >
                <Text style={[styles.chipText, isSelected && styles.selectedChipText]}>
                  {tier.toUpperCase()}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#111111",
    marginBottom: 10,
    letterSpacing: 0.3,
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    backgroundColor: "#f9fafb",
  },
  selectedChip: {
    backgroundColor: "#111111",
    borderColor: "#111111",
  },
  chipText: {
    fontSize: 13,
    color: "#374151",
    fontWeight: "500",
  },
  selectedChipText: {
    color: "#ffffff",
    fontWeight: "600",
  },
});
