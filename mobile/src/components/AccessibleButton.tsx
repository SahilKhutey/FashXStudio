import React from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  type ViewStyle,
} from "react-native";
import { accessibility } from "../design-system/tokens/accessibility";

type Props = {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
  accessibilityHint?: string;
  style?: ViewStyle;
};

export function AccessibleButton({
  label,
  onPress,
  disabled = false,
  loading = false,
  accessibilityHint,
  style,
}: Props) {
  const unavailable = disabled || loading;

  return (
    <Pressable
      onPress={onPress}
      disabled={unavailable}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityHint={accessibilityHint}
      accessibilityState={{
        disabled: unavailable,
        busy: loading,
      }}
      style={[styles.button, unavailable && styles.disabled, style]}
    >
      {loading ? (
        <ActivityIndicator
          color="#FFFFFF"
          accessibilityLabel={`${label}, loading`}
        />
      ) : (
        <Text allowFontScaling style={styles.label}>
          {label}
        </Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: accessibility.recommendedTouchTarget,
    minWidth: accessibility.recommendedTouchTarget,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: "#111827",
    justifyContent: "center",
    alignItems: "center",
  },
  disabled: {
    opacity: 0.55,
  },
  label: {
    fontSize: 16,
    fontWeight: "600",
    color: "#FFFFFF",
  },
});
