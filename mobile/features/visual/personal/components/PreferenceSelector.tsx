import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";

interface PreferenceSelectorProps {
  options: string[];
  selectedOptions: string[];
  onToggleOption: (option: string) => void;
  testID?: string;
}

export const PreferenceSelector: React.FC<PreferenceSelectorProps> = ({
  options,
  selectedOptions,
  onToggleOption,
  testID = "preference-selector",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      {options.map((option) => {
        const isSelected = selectedOptions.includes(option);
        return (
          <TouchableOpacity
            key={option}
            testID={`option-${option.toLowerCase().replace(/\s+/g, "-")}`}
            style={[styles.chip, isSelected ? styles.selectedChip : styles.unselectedChip]}
            onPress={() => onToggleOption(option)}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: isSelected }}
            accessibilityLabel={`${option}, ${isSelected ? "selected" : "not selected"}`}
          >
            <Text
              style={[
                styles.chipText,
                isSelected ? styles.selectedChipText : styles.unselectedChipText,
              ]}
            >
              {option} {isSelected ? "✓" : ""}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    flexDirection: "row",
    alignItems: "center",
  },
  selectedChip: {
    backgroundColor: "#1C1C1E",
    borderColor: "#1C1C1E",
  },
  unselectedChip: {
    backgroundColor: "#F2F2F7",
    borderColor: "#E5E5EA",
  },
  chipText: {
    fontSize: 13,
    fontWeight: "600",
  },
  selectedChipText: {
    color: "#FFFFFF",
  },
  unselectedChipText: {
    color: "#1C1C1E",
  },
});
