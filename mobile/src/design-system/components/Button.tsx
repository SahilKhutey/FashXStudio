import React from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  ViewStyle,
} from "react-native";
import { AppText } from "./AppText";
import { useDesignTokens } from "../useDesignTokens";

export type ButtonProps = {
  title: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "outline" | "danger";
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  accessibilityLabel?: string;
};

export function Button({
  title,
  onPress,
  variant = "primary",
  loading = false,
  disabled = false,
  style,
  accessibilityLabel,
}: ButtonProps) {
  const { colors, spacing, radius } = useDesignTokens();

  const backgroundColor = {
    primary: colors.brand,
    secondary: colors.surfaceSecondary,
    outline: "transparent",
    danger: colors.danger,
  }[variant];

  const textColor =
    variant === "primary" || variant === "danger"
      ? "textOnBrand"
      : "textPrimary";

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? title}
      accessibilityState={{ disabled: disabled || loading, busy: loading }}
      disabled={disabled || loading}
      onPress={onPress}
      style={[
        styles.button,
        {
          backgroundColor,
          borderRadius: radius.md,
          paddingHorizontal: spacing[4],
          paddingVertical: spacing[3],
          borderWidth: variant === "outline" ? 1 : 0,
          borderColor: colors.borderStrong,
          opacity: disabled ? 0.5 : 1,
        },
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator
          color={
            variant === "primary" || variant === "danger"
              ? colors.textOnBrand
              : colors.brand
          }
        />
      ) : (
        <AppText variant="button" color={textColor}>
          {title}
        </AppText>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 48,
    alignItems: "center",
    justifyContent: "center",
  },
});
