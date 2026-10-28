import React from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { useTranslation } from "react-i18next";
import { AppText } from "../../design-system/components/AppText";
import { useDesignTokens } from "../../design-system/useDesignTokens";

type LoadingStateProps = {
  message?: string;
  compact?: boolean;
};

export function LoadingState({ message, compact = false }: LoadingStateProps) {
  const { t } = useTranslation();
  const { colors, spacing } = useDesignTokens();

  if (compact) {
    return (
      <View
        style={[styles.compactContainer, { paddingVertical: spacing[4], gap: spacing[2] }]}
        accessibilityRole="progressbar"
        accessibilityLabel={message ?? t("common.loading")}
      >
        <ActivityIndicator size="small" color={colors.brand} />
        {message ? (
          <AppText variant="caption" color="textMuted">
            {message}
          </AppText>
        ) : null}
      </View>
    );
  }

  return (
    <View
      style={[styles.container, { backgroundColor: colors.background }]}
      accessibilityRole="progressbar"
      accessibilityLabel={message ?? t("common.loading")}
    >
      <ActivityIndicator size="large" color={colors.brand} />
      <View style={{ height: spacing[3] }} />
      <AppText color="textSecondary">
        {message ?? t("common.loading")}
      </AppText>
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
  compactContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
  },
});
