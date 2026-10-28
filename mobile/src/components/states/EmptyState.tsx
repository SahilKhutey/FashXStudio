import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { useTranslation } from "react-i18next";
import { AppText } from "../../design-system/components/AppText";
import { useDesignTokens } from "../../design-system/useDesignTokens";

type EmptyStateProps = {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: string;
};

export function EmptyState({
  title,
  message,
  actionLabel,
  onAction,
  icon,
}: EmptyStateProps) {
  const { t } = useTranslation();
  const { colors, spacing, radius } = useDesignTokens();

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {icon ? (
        <>
          <AppText style={styles.icon}>{icon}</AppText>
          <View style={{ height: spacing[2] }} />
        </>
      ) : null}

      <AppText variant="heading3" style={styles.textCenter}>
        {title}
      </AppText>

      <View style={{ height: spacing[2] }} />

      <AppText color="textSecondary" style={styles.textCenter}>
        {message}
      </AppText>

      {actionLabel && onAction ? (
        <>
          <View style={{ height: spacing[4] }} />
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={actionLabel}
            onPress={onAction}
            style={{
              backgroundColor: colors.brand,
              paddingHorizontal: spacing[5],
              paddingVertical: spacing[3],
              borderRadius: radius.md,
            }}
          >
            <AppText color="textOnBrand" variant="button">
              {actionLabel || t("common.continue")}
            </AppText>
          </Pressable>
        </>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  icon: {
    fontSize: 48,
  },
  textCenter: {
    textAlign: "center",
  },
});
