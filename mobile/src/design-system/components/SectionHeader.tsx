import React from "react";
import { Pressable, StyleSheet, View, type ViewStyle } from "react-native";
import { AppText } from "./AppText";
import { useDesignTokens } from "../useDesignTokens";

export type SectionHeaderProps = {
  title: string;
  subtitle?: string;
  actionLabel?: string;
  onAction?: () => void;
  style?: ViewStyle;
};

export function SectionHeader({
  title,
  subtitle,
  actionLabel,
  onAction,
  style,
}: SectionHeaderProps) {
  const { spacing } = useDesignTokens();

  return (
    <View style={[styles.container, { marginBottom: spacing[3] }, style]}>
      <View style={styles.textContainer}>
        <AppText variant="heading3" numberOfLines={1}>
          {title}
        </AppText>
        {subtitle && (
          <AppText variant="caption" color="textSecondary" style={{ marginTop: 2 }}>
            {subtitle}
          </AppText>
        )}
      </View>
      {actionLabel && onAction && (
        <Pressable
          onPress={onAction}
          accessibilityRole="button"
          accessibilityLabel={actionLabel}
          style={styles.actionButton}
        >
          <AppText variant="label" color="textPrimary">
            {actionLabel}
          </AppText>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  textContainer: {
    flex: 1,
  },
  actionButton: {
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
});
