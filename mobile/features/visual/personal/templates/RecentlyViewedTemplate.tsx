import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { RecentlyViewedTemplateSpecContract } from "../types";
import { RecentItem } from "../components/RecentItem";

interface RecentlyViewedTemplateProps {
  data: RecentlyViewedTemplateSpecContract;
  onFilterChange?: (entityType: string | null) => void;
  onClearHistory?: () => void;
  onOpenItem?: (id: string, type: string) => void;
  onStartExploring?: () => void;
  testID?: string;
}

export const RecentlyViewedTemplate: React.FC<RecentlyViewedTemplateProps> = ({
  data,
  onFilterChange,
  onClearHistory,
  onOpenItem,
  onStartExploring,
  testID = "recently-viewed-pr07",
}) => {
  const filterTabs = [
    { key: null, label: "All" },
    { key: "product", label: "Products" },
    { key: "look", label: "Looks" },
    { key: "fashion", label: "Fashion" },
    { key: "trend", label: "Trends" },
  ];

  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Text style={styles.title}>Recently Viewed ({data.total_count})</Text>
          {data.can_clear_history && data.items.length > 0 && (
            <TouchableOpacity
              testID="clear-history-button"
              onPress={onClearHistory}
              accessibilityRole="button"
              accessibilityLabel="Clear history"
            >
              <Text style={styles.clearText}>Clear History</Text>
            </TouchableOpacity>
          )}
        </View>

        <Text style={styles.privacyNotice}>
          Viewing history helps you retrace steps. Browsing does not imply endorsement or change explicit preferences.
        </Text>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filtersBar}>
          {filterTabs.map((tab) => {
            const isActive = data.active_filter === tab.key;
            return (
              <TouchableOpacity
                key={tab.label}
                testID={`filter-${tab.label.toLowerCase()}`}
                style={[styles.filterChip, isActive && styles.activeFilterChip]}
                onPress={() => onFilterChange && onFilterChange(tab.key)}
              >
                <Text
                  style={[styles.filterText, isActive && styles.activeFilterText]}
                >
                  {tab.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {data.items.length === 0 ? (
        <View testID="empty-recently-viewed" style={styles.emptyState}>
          <Text style={styles.emptyTitle}>Nothing viewed recently.</Text>
          <TouchableOpacity
            testID="start-exploring-button"
            style={styles.exploreBtn}
            onPress={onStartExploring}
            accessibilityRole="button"
            accessibilityLabel="Start Exploring"
          >
            <Text style={styles.exploreBtnText}>Start Exploring</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.list}>
          {data.items.map((act) => (
            <RecentItem
              key={`${act.entity_id}-${act.timestamp}`}
              activity={act}
              onOpen={onOpenItem}
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
  titleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  title: {
    fontSize: 20,
    fontWeight: "700",
    color: "#1C1C1E",
  },
  clearText: {
    fontSize: 13,
    color: "#D70015",
    fontWeight: "600",
  },
  privacyNotice: {
    fontSize: 11,
    color: "#8E8E93",
    lineHeight: 15,
    marginVertical: 6,
  },
  filtersBar: {
    flexDirection: "row",
    marginTop: 6,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: "#F2F2F7",
    marginRight: 8,
  },
  activeFilterChip: {
    backgroundColor: "#1C1C1E",
  },
  filterText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#636366",
  },
  activeFilterText: {
    color: "#FFFFFF",
  },
  list: {
    padding: 16,
    backgroundColor: "#FFFFFF",
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
