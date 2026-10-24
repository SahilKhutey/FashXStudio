import React from "react";
import { StyleSheet, Text, View, TouchableOpacity } from "react-native";
import { useTranslation } from "react-i18next";
import { useConfig } from "../../src/api/hooks";

export default function MaintenanceScreen() {
  const { t } = useTranslation();
  const { refetch, isFetching } = useConfig();

  return (
    <View style={styles.container} testID="maintenance-screen">
      <View style={styles.content}>
        <Text style={styles.badge}>MAINTENANCE</Text>
        <Text style={styles.title} accessibilityRole="header">
          {t("config.maintenanceTitle")}
        </Text>
        <Text style={styles.message}>
          {t("config.maintenanceMessage")}
        </Text>
        <TouchableOpacity
          style={[styles.button, isFetching && styles.buttonDisabled]}
          onPress={() => refetch()}
          disabled={isFetching}
          accessibilityRole="button"
          accessibilityLabel={t("common.retry")}
        >
          <Text style={styles.buttonText}>
            {isFetching ? t("common.loading") : t("common.retry")}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F9FAFB",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  content: {
    maxWidth: 400,
    width: "100%",
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 28,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  badge: {
    fontSize: 11,
    fontWeight: "700",
    color: "#D97706",
    backgroundColor: "#FEF3C7",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    marginBottom: 16,
    letterSpacing: 0.5,
  },
  title: {
    fontSize: 20,
    fontWeight: "700",
    color: "#111827",
    textAlign: "center",
    marginBottom: 12,
  },
  message: {
    fontSize: 14,
    color: "#4B5563",
    textAlign: "center",
    lineHeight: 20,
    marginBottom: 24,
  },
  button: {
    backgroundColor: "#4F46E5",
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
    width: "100%",
    alignItems: "center",
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "600",
  },
});
