import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { useTranslation } from "react-i18next";
import { AppText } from "../../design-system/components/AppText";
import { useDesignTokens } from "../../design-system/useDesignTokens";

type ErrorStateProps = {
  title?: string;
  message?: string;
  onRetry: () => void;
  retrying?: boolean;
};

export function ErrorState({
  title,
  message,
  onRetry,
  retrying = false,
}: ErrorStateProps) {
  const { t } = useTranslation();
  const { colors, spacing, radius } = useDesignTokens();

  return (
    <View
      style={[styles.container, { backgroundColor: colors.background }]}
      accessibilityRole="alert"
    >
      <AppText variant="heading3">
        {title ?? t("common.error")}
      </AppText>

      <View style={{ height: spacing[2] }} />

      <AppText color="textSecondary">
        {message ?? t("common.networkError")}
      </AppText>

      <View style={{ height: spacing[4] }} />

      <Pressable
        accessibilityRole="button"
        accessibilityLabel={t("common.retry")}
        accessibilityState={{ disabled: retrying, busy: retrying }}
        disabled={retrying}
        onPress={onRetry}
        style={{
          backgroundColor: colors.brand,
          paddingHorizontal: spacing[5],
          paddingVertical: spacing[3],
          borderRadius: radius.md,
          opacity: retrying ? 0.6 : 1,
        }}
      >
        <AppText color="textOnBrand" variant="button">
          {t("common.retry")}
        </AppText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
});
