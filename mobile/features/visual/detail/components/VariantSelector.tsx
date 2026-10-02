import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { VariantGroupContract, VariantOptionItemContract } from "../types";

interface VariantSelectorProps {
  groups: VariantGroupContract[];
  selectedVariants: Record<string, string>; // group_id -> option_id
  onSelectOption: (groupId: string, optionId: string) => void;
  testID?: string;
}

export const VariantSelector: React.FC<VariantSelectorProps> = ({
  groups = [],
  selectedVariants,
  onSelectOption,
  testID = "variant-selector",
}) => {
  if (groups.length === 0) return null;

  return (
    <View testID={testID} style={styles.container}>
      {groups.map((group) => {
        const selectedId = selectedVariants[group.group_id] || group.selected_option_id;

        return (
          <View key={group.group_id} style={styles.groupContainer}>
            <View style={styles.headerRow}>
              <Text style={styles.groupName}>{group.name}</Text>
              {selectedId && (
                <Text style={styles.selectedLabel}>
                  {group.options.find((o) => o.id === selectedId)?.label}
                </Text>
              )}
            </View>

            <View style={styles.optionsRow}>
              {group.options.map((option) => {
                const isSelected = option.id === selectedId;
                const isUnavailable = option.state === "unavailable";
                const isColor = Boolean(option.swatch_hex);

                return (
                  <TouchableOpacity
                    key={option.id}
                    testID={`${testID}-${group.group_id}-${option.id}`}
                    disabled={isUnavailable}
                    onPress={() => onSelectOption(group.group_id, option.id)}
                    style={[
                      isColor ? styles.colorSwatch : styles.sizePill,
                      isSelected && styles.optionSelected,
                      isUnavailable && styles.optionUnavailable,
                    ]}
                    accessibilityRole="button"
                    accessibilityState={{ selected: isSelected, disabled: isUnavailable }}
                    accessibilityLabel={`${option.label} ${isUnavailable ? "out of stock" : ""}`}
                  >
                    {isColor && option.swatch_hex ? (
                      <View
                        style={[
                          styles.swatchInner,
                          { backgroundColor: option.swatch_hex },
                          isSelected && styles.swatchInnerSelected,
                        ]}
                      />
                    ) : (
                      <Text
                        style={[
                          styles.optionText,
                          isSelected && styles.optionTextSelected,
                          isUnavailable && styles.optionTextUnavailable,
                        ]}
                      >
                        {option.label}
                      </Text>
                    )}
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
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: "#eeeeee",
  },
  groupContainer: {
    marginBottom: 16,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  groupName: {
    fontSize: 14,
    fontWeight: "700",
    color: "#222222",
  },
  selectedLabel: {
    fontSize: 13,
    color: "#666666",
    fontWeight: "500",
  },
  optionsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  sizePill: {
    minWidth: 48,
    height: 40,
    paddingHorizontal: 14,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: "#dddddd",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#ffffff",
  },
  colorSwatch: {
    width: 38,
    height: 38,
    borderRadius: 19,
    borderWidth: 2,
    borderColor: "#dddddd",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#ffffff",
  },
  swatchInner: {
    width: 28,
    height: 28,
    borderRadius: 14,
  },
  swatchInnerSelected: {
    width: 26,
    height: 26,
  },
  optionSelected: {
    borderColor: "#111111",
    backgroundColor: "#f9f9f9",
  },
  optionUnavailable: {
    borderColor: "#eeeeee",
    backgroundColor: "#fafafa",
    opacity: 0.45,
  },
  optionText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333333",
  },
  optionTextSelected: {
    color: "#111111",
    fontWeight: "700",
  },
  optionTextUnavailable: {
    color: "#999999",
    textDecorationLine: "line-through",
  },
});
