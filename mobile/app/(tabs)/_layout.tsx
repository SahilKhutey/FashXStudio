import React from "react";
import { Tabs, useRouter } from "expo-router";
import { Pressable, StyleSheet, Text } from "react-native";
import { useDesignTokens } from "../../src/design-system";

export default function TabLayout() {
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
        headerRight: () => (
          <Pressable
            onPress={() => router.push("/settings")}
            accessibilityRole="button"
            accessibilityLabel="Open settings"
            style={styles.headerButton}
          >
            <Text style={styles.headerButtonIcon}>⚙</Text>
          </Pressable>
        ),
      }}
    >
      <Tabs.Screen
        name="feed"
        options={{
          title: "Discover",
          tabBarLabel: "Home",
          tabBarIcon: ({ color }) => (
            <Text style={{ color, fontSize: 18 }} accessible={false}>
              ✦
            </Text>
          ),
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: "Explore",
          tabBarLabel: "Explore",
          tabBarIcon: ({ color }) => (
            <Text style={{ color, fontSize: 18 }} accessible={false}>
              ⌕
            </Text>
          ),
        }}
      />
      <Tabs.Screen
        name="looks"
        options={{
          title: "Your Looks",
          tabBarLabel: "Looks",
          tabBarIcon: ({ color }) => (
            <Text style={{ color, fontSize: 18 }} accessible={false}>
              ▧
            </Text>
          ),
        }}
      />
      <Tabs.Screen
        name="closet"
        options={{
          title: "My Closet",
          tabBarLabel: "Closet",
          tabBarIcon: ({ color }) => (
            <Text style={{ color, fontSize: 18 }} accessible={false}>
              ♧
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
    padding: 8,
  },
  headerButtonIcon: {
    fontSize: 20,
  },
});
