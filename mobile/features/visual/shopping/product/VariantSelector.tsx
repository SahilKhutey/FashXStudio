/**
 * VariantSelector Component — Phase 07 (Section 7.25 - 7.27).
 *
 * Renders variant groups (Size, Color, Material) with selectable pills,
 * visual swatch circles, disabled states, and selection callbacks.
 */

import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { ProductVariantGroup, ProductVariantOption } from "../types";

export interface VariantSelectorProps {
  groups: ProductVariantGroup[];
  selectedVariants: Record<string, string>;
  onSelectVariant: (groupType: string, optionValue: string) => void;
}

export const VariantSelector: React.FC<VariantSelectorProps> = ({
  groups,
  selectedVariants,
  onSelectVariant,
}) => {
  return (
    <View style={styles.container}>
      {groups.map((group) => {
        const selectedValue = selectedVariants[group.variantType];

        return (
          <View key={group.id} style={styles.groupContainer}>
            <View style={styles.groupHeader}>
              <Text style={styles.groupTitle}>{group.title}</Text>
              {selectedValue ? (
                <Text style={styles.selectedValue}>{selectedValue.toUpperCase()}</Text>
              ) : null}
            </View>

            <View style={styles.optionsRow}>
              {group.options.map((option) => {
                const isSelected = selectedValue === option.value || option.state === "selected";
                const isUnavailable = option.state === "unavailable";
                const isDisabled = option.state === "disabled" || isUnavailable;

                if (group.variantType === "color" && option.swatchHex) {
                  return (
                    <TouchableOpacity
                      key={option.id}
                      accessibilityLabel={`Select color ${option.label}`}
                      disabled={isDisabled}
                      onPress={() => onSelectVariant(group.variantType, option.value)}
                      style={[
                        styles.swatchButton,
                        isSelected && styles.swatchSelected,
                        isDisabled && styles.swatchDisabled,
                      ]}
                    >
                      <View style={[styles.swatchCircle, { backgroundColor: option.swatchHex }]} />
                    </TouchableOpacity>
                  );
                }

                return (
                  <TouchableOpacity
                    key={option.id}
                    accessibilityLabel={`Select ${group.title} ${option.label}`}
                    disabled={isDisabled}
                    onPress={() => onSelectVariant(group.variantType, option.value)}
                    style={[
                      styles.pillButton,
                      isSelected && styles.pillSelected,
                      isUnavailable && styles.pillUnavailable,
                    ]}
                  >
                    <Text
                      style={[
                        styles.pillText,
                        isSelected && styles.pillTextSelected,
                        isUnavailable && styles.pillTextUnavailable,
                      ]}
                    >
                      {option.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    gap: 16,
    marginVertical: 8,
  },
  groupContainer: {
    gap: 8,
  },
  groupHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  groupTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  selectedValue: {
    fontSize: 12,
    fontWeight: "600",
    color: defaultDesignTokens.brand.primary,
  },
  optionsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  pillButton: {
    minWidth: 44,
    height: 44,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: defaultDesignTokens.neutral.neutral300,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
    justifyContent: "center",
    alignItems: "center",
  },
  pillSelected: {
    borderColor: defaultDesignTokens.brand.primary,
    backgroundColor: defaultDesignTokens.brand.primary,
  },
  pillUnavailable: {
    borderColor: defaultDesignTokens.neutral.neutral200,
    backgroundColor: defaultDesignTokens.neutral.neutral100,
    opacity: 0.6,
  },
  pillText: {
    fontSize: 13,
    fontWeight: "600",
    color: defaultDesignTokens.neutral.neutral800,
  },
  pillTextSelected: {
    color: defaultDesignTokens.surfaces.surfaceLight,
  },
  pillTextUnavailable: {
    color: defaultDesignTokens.neutral.neutral400,
    textDecorationLine: "line-through",
  },
  swatchButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 2,
    borderColor: "transparent",
    justifyContent: "center",
    alignItems: "center",
  },
  swatchSelected: {
    borderColor: defaultDesignTokens.brand.primary,
  },
  swatchDisabled: {
    opacity: 0.3,
  },
  swatchCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
  },
});
