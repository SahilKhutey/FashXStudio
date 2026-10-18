import React from "react";
import { Tabs, useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { StyleSheet, Text, TouchableOpacity } from "react-native";

export default function TabLayout() {
  const { t } = useTranslation();
  const router = useRouter();

  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        headerStyle: styles.header,
        headerTitleStyle: styles.headerTitle,
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
        tabBarActiveTintColor: "#4F46E5",
        tabBarInactiveTintColor: "#6B7280",
        tabBarStyle: styles.tabBar,
        tabBarLabelStyle: styles.tabBarLabel,
      }}
    >
      <Tabs.Screen
        name="feed"
        options={{
          title: t("feed.title"),
          tabBarLabel: t("tabs.feed"),
          tabBarIcon: ({ color }) => (
            <Text style={{ color, fontSize: 18 }} accessibilityElementsHidden>
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
            <Text style={{ color, fontSize: 18 }} accessibilityElementsHidden>
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
            <Text style={{ color, fontSize: 18 }} accessibilityElementsHidden>
              👗
            </Text>
          ),
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  header: {
    backgroundColor: "#FFFFFF",
    elevation: 1,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
  },
  headerButton: {
    marginRight: 16,
    padding: 6,
  },
  headerButtonIcon: {
    fontSize: 18,
  },
  tabBar: {
    backgroundColor: "#FFFFFF",
    borderTopColor: "#E5E7EB",
    borderTopWidth: 1,
    height: 60,
    paddingBottom: 8,
    paddingTop: 6,
  },
  tabBarLabel: {
    fontSize: 12,
    fontWeight: "600",
  },
});
