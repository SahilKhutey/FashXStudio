import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { SavedFashionTemplateSpecContract } from "../types";
import { SavedFashionCard } from "../components/SavedFashionCard";

interface SavedFashionTemplateProps {
  data: SavedFashionTemplateSpecContract;
  onTabChange?: (tab: string) => void;
  onOpenFashion?: (contentId: string) => void;
  onRemoveFashion?: (id: string) => void;
  onExploreFashion?: () => void;
  testID?: string;
}

export const SavedFashionTemplate: React.FC<SavedFashionTemplateProps> = ({
  data,
  onTabChange,
  onOpenFashion,
  onRemoveFashion,
  onExploreFashion,
  testID = "saved-fashion-pr05",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Saved Fashion ({data.total_count})</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabsBar}>
          {data.available_tabs.map((tab) => {
            const isActive = data.active_tab === tab;
            return (
              <TouchableOpacity
                key={tab}
                testID={`tab-${tab}`}
                style={[styles.tabChip, isActive && styles.activeTabChip]}
                onPress={() => onTabChange && onTabChange(tab)}
              >
                <Text style={[styles.tabText, isActive && styles.activeTabText]}>
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {data.items.length === 0 ? (
        <View testID="empty-saved-fashion" style={styles.emptyState}>
          <Text style={styles.emptyTitle}>No saved fashion content yet.</Text>
          <TouchableOpacity
            testID="explore-fashion-button"
            style={styles.exploreBtn}
            onPress={onExploreFashion}
            accessibilityRole="button"
            accessibilityLabel="Explore Fashion"
          >
            <Text style={styles.exploreBtnText}>Explore Fashion</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.list}>
          {data.items.map((item) => (
            <SavedFashionCard
              key={item.id}
              fashion={item}
              onOpen={onOpenFashion}
              onRemove={onRemoveFashion}
            />
          ))}
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F2F2F7",
  },
  header: {
    padding: 16,
    backgroundColor: "#FFFFFF",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  title: {
    fontSize: 20,
    fontWeight: "700",
    color: "#1C1C1E",
    marginBottom: 8,
  },
  tabsBar: {
    flexDirection: "row",
  },
  tabChip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: "#F2F2F7",
    marginRight: 8,
  },
  activeTabChip: {
    backgroundColor: "#1C1C1E",
  },
  tabText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#636366",
  },
  activeTabText: {
    color: "#FFFFFF",
  },
  list: {
    padding: 16,
  },
  emptyState: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1C1C1E",
    marginBottom: 16,
  },
  exploreBtn: {
    backgroundColor: "#1C1C1E",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  exploreBtnText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
});
