import React from "react";
import { Pressable, StyleSheet, type ViewStyle } from "react-native";
import { AppText } from "./AppText";
import { useDesignTokens } from "../useDesignTokens";

export type CategoryChipProps = {
  label: string;
  selected?: boolean;
  onPress: () => void;
  style?: ViewStyle;
};

export function CategoryChip({
  label,
  selected = false,
  onPress,
  style,
}: CategoryChipProps) {
  const { colors, radius, spacing } = useDesignTokens();

  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`Filter by ${label}`}
      accessibilityState={{ selected }}
      style={[
        styles.chip,
        {
          backgroundColor: selected ? colors.brand : colors.surfaceSecondary,
          borderColor: selected ? colors.brand : colors.border,
          borderRadius: radius.pill,
          paddingHorizontal: spacing[4],
          paddingVertical: spacing[2],
        },
        style,
      ]}
    >
      <AppText
        variant="label"
        color={selected ? "textOnBrand" : "textPrimary"}
      >
        {label}
      </AppText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
});
