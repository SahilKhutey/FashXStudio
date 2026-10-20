import React from "react";
import { Pressable, Text, StyleSheet } from "react-native";

export interface ChipProps {
  label: string;
  selected: boolean;
  onPress?: () => void;
  accessibilityRole?: "button" | "checkbox";
}

export function Chip({ label, selected, onPress, accessibilityRole = "button" }: ChipProps) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole={accessibilityRole}
      accessibilityState={{ selected }}
      style={[styles.chip, selected && styles.chipSelected]}
    >
      <Text style={[styles.label, selected && styles.labelSelected]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    backgroundColor: "#F9FAFB",
    marginRight: 8,
    marginBottom: 8,
  },
  chipSelected: {
    borderColor: "#4F46E5",
    backgroundColor: "#EEF2FF",
  },
  label: {
    fontSize: 14,
    color: "#374151",
    fontWeight: "500",
  },
  labelSelected: {
    color: "#4F46E5",
    fontWeight: "600",
  },
});
