import React from "react";
import { StyleSheet, Text, View, TouchableOpacity, Linking, Platform } from "react-native";
import { useTranslation } from "react-i18next";

export default function UpdateRequiredScreen() {
  const { t } = useTranslation();

  const handleUpdate = () => {
    // Open platform app store or release page
    const storeUrl =
      Platform.OS === "ios"
        ? "https://apps.apple.com"
        : "https://play.google.com/store/apps";
    Linking.openURL(storeUrl).catch(() => {});
  };

  return (
    <View style={styles.container} testID="update-required-screen">
      <View style={styles.content}>
        <Text style={styles.badge}>UPDATE REQUIRED</Text>
        <Text style={styles.title} accessibilityRole="header">
          {t("config.updateRequired")}
        </Text>
        <Text style={styles.message}>
          {t("config.updateMessage")}
        </Text>
        <TouchableOpacity
          style={styles.button}
          onPress={handleUpdate}
          accessibilityRole="button"
          accessibilityLabel={t("config.updateButton")}
        >
          <Text style={styles.buttonText}>{t("config.updateButton")}</Text>
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
    color: "#DC2626",
    backgroundColor: "#FEE2E2",
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
  buttonText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "600",
  },
});
