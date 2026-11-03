import React from "react";
import { StyleSheet, View, type ViewStyle } from "react-native";
import { AppText } from "./AppText";
import { useDesignTokens } from "../useDesignTokens";

export type BadgeProps = {
  label: string;
  variant?: "brand" | "neutral" | "success" | "warning" | "danger";
  style?: ViewStyle;
};

export function Badge({ label, variant = "brand", style }: BadgeProps) {
  const { colors, radius, spacing } = useDesignTokens();

  const backgroundColor = {
    brand: colors.brand,
    neutral: colors.surfaceSecondary,
    success: colors.success,
    warning: colors.warning,
    danger: colors.danger,
  }[variant];

  const textColor = variant === "neutral" ? "textPrimary" : "textOnBrand";

  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor,
          borderRadius: radius.sm,
          paddingHorizontal: spacing[2],
          paddingVertical: 2,
        },
        style,
      ]}
    >
      <AppText variant="caption" color={textColor}>
        {label}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: "flex-start",
    alignItems: "center",
    justifyContent: "center",
  },
});
