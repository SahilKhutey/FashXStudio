import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";

interface SettingsNavigationProps {
  categories: string[];
  activeCategory: string;
  onSelectCategory: (category: string) => void;
  onSignOut?: () => void;
  testID?: string;
}

export const SettingsNavigation: React.FC<SettingsNavigationProps> = ({
  categories,
  activeCategory,
  onSelectCategory,
  onSignOut,
  testID = "settings-navigation",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <Text style={styles.header}>SETTINGS & CONTROLS</Text>
      {categories.map((cat) => {
        const isActive = activeCategory === cat;
        return (
          <TouchableOpacity
            key={cat}
            testID={`setting-cat-${cat}`}
            style={[styles.row, isActive && styles.activeRow]}
            onPress={() => onSelectCategory(cat)}
            accessibilityRole="button"
            accessibilityLabel={cat}
          >
            <Text style={[styles.label, isActive && styles.activeLabel]}>
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </Text>
            <Text style={styles.chevron}>›</Text>
          </TouchableOpacity>
        );
      })}

      {onSignOut && (
        <TouchableOpacity
          testID="sign-out-button"
          style={styles.signOutBtn}
          onPress={onSignOut}
          accessibilityRole="button"
          accessibilityLabel="Sign out"
        >
          <Text style={styles.signOutText}>Sign Out</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    marginVertical: 8,
    overflow: "hidden",
  },
  header: {
    fontSize: 11,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    padding: 16,
    paddingBottom: 8,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  activeRow: {
    backgroundColor: "#F2F2F7",
  },
  label: {
    fontSize: 15,
    fontWeight: "500",
    color: "#1C1C1E",
  },
  activeLabel: {
    fontWeight: "700",
    color: "#007AFF",
  },
  chevron: {
    fontSize: 18,
    color: "#C7C7CC",
    fontWeight: "600",
  },
  signOutBtn: {
    padding: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
    alignItems: "center",
  },
  signOutText: {
    color: "#D70015",
    fontSize: 14,
    fontWeight: "600",
  },
});
