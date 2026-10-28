import React from "react";
import { Tabs, useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { StyleSheet, Text, TouchableOpacity } from "react-native";
import { useDesignTokens } from "../../src/design-system";

export default function TabLayout() {
  const { t } = useTranslation();
  const router = useRouter();
  const { colors, spacing } = useDesignTokens();

  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        headerStyle: {
          backgroundColor: colors.surface,
          elevation: 1,
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 1 },
          shadowOpacity: 0.05,
          shadowRadius: 2,
        },
        headerTitleStyle: {
          color: colors.textPrimary,
          fontSize: 18,
          fontWeight: "700",
        },
        headerTintColor: colors.textPrimary,
        headerRight: () => (
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => router.push("/settings")}
            accessibilityRole="button"
            accessibilityLabel="Settings"
          >
            <Text style={styles.headerButtonIcon}>⚙️</Text>
          </TouchableOpacity>
        ),
        tabBarActiveTintColor: colors.brand,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          borderTopWidth: 1,
          height: 64,
          paddingTop: spacing[2],
          paddingBottom: spacing[2],
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: "600",
        },
      }}
    >
      <Tabs.Screen
        name="feed"
        options={{
          title: t("feed.title"),
          tabBarLabel: t("tabs.feed"),
          tabBarIcon: ({ color }) => (
            <Text style={{ color, fontSize: 18 }} accessible={false}>
              ✨
            </Text>
          ),
        }}
      />

      <Tabs.Screen
        name="looks"
        options={{
          title: t("looks.title"),
          tabBarLabel: t("tabs.looks"),
          tabBarIcon: ({ color }) => (
            <Text style={{ color, fontSize: 18 }} accessible={false}>
              📸
            </Text>
          ),
        }}
      />

      <Tabs.Screen
        name="closet"
        options={{
          title: t("tabs.closet"),
          tabBarLabel: t("tabs.closet"),
          tabBarIcon: ({ color }) => (
            <Text style={{ color, fontSize: 18 }} accessible={false}>
              👗
            </Text>
          ),
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  headerButton: {
    marginRight: 16,
    padding: 6,
  },
  headerButtonIcon: {
    fontSize: 18,
  },
});
