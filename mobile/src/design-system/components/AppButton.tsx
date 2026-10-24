import React from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  type PressableProps,
  type ViewStyle,
} from "react-native";
import { useDesignTokens } from "../useDesignTokens";
import { AppText } from "./AppText";
import { accessibility } from "../tokens/accessibility";
import { radius, spacing } from "../tokens/primitives";

type AppButtonProps = Omit<PressableProps, "children" | "style"> & {
  label: string;
  variant?: "primary" | "secondary" | "outline";
  loading?: boolean;
  fullWidth?: boolean;
  style?: ViewStyle;
};

export function AppButton({
  label,
  variant = "primary",
  loading = false,
  disabled = false,
  fullWidth = false,
  style,
  ...props
}: AppButtonProps) {
  const { colors, opacity: opacityTokens } = useDesignTokens();

  const backgroundColor =
    variant === "primary"
      ? colors.brand
      : variant === "secondary"
        ? colors.surfaceSecondary
        : "transparent";

  const borderColor =
    variant === "outline" ? colors.borderStrong : "transparent";

  const textColor =
    variant === "primary" ? "textOnBrand" : "textPrimary";

  const buttonStyle = ({ pressed }: { pressed: boolean }): ViewStyle => ({
    backgroundColor,
    borderColor,
    borderWidth: variant === "outline" ? 1 : 0,
    opacity: disabled ? opacityTokens.disabled : 1,
    transform: [{ scale: pressed && !disabled ? 0.98 : 1 }],
  });

  return (
    <Pressable
      {...props}
      accessibilityRole="button"
      accessibilityLabel={props.accessibilityLabel ?? label}
      accessibilityState={{ disabled: disabled || loading, busy: loading }}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.base,
        fullWidth && styles.fullWidth,
        buttonStyle({ pressed }),
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator
          color={variant === "primary" ? colors.textOnBrand : colors.textPrimary}
        />
      ) : (
        <AppText variant="button" color={textColor}>
          {label}
        </AppText>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: accessibility.minimumTouchTarget,
    paddingHorizontal: spacing[4],
    paddingVertical: spacing[3],
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
  },
  fullWidth: {
    width: "100%",
  },
});
