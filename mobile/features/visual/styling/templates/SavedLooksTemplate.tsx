import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { SavedLooksTemplateSpecContract } from "../types";
import { SavedLookCard } from "../components/SavedLookCard";

interface SavedLooksTemplateProps {
  data: SavedLooksTemplateSpecContract;
  onPressLook?: (lookId: string) => void;
  onDuplicateLook?: (lookId: string) => void;
  onDeleteLook?: (lookId: string) => void;
  onSelectFilter?: (filter: string) => void;
  currency?: string;
  testID?: string;
}

export const SavedLooksTemplate: React.FC<SavedLooksTemplateProps> = ({
  data,
  onPressLook,
  onDuplicateLook,
  onDeleteLook,
  onSelectFilter,
  currency = "INR",
  testID = "saved-looks-screen",
}) => {
  const filters = ["all", "minimal", "streetwear", "formal", "favorites"];

  return (
    <View testID={testID} style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Saved Looks</Text>
        <Text style={styles.subtitle}>{data.total_saved} saved outfits in your collection</Text>
      </View>

      {/* Filter Tabs */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filterBar}
      >
        {filters.map((f) => {
          const isSelected = data.active_filter === f;
          return (
            <TouchableOpacity
              key={f}
              testID={`filter-tab-${f}`}
              style={[styles.filterChip, isSelected && styles.activeFilterChip]}
              onPress={() => onSelectFilter?.(f)}
            >
              <Text
                style={[styles.filterText, isSelected && styles.activeFilterText]}
              >
                {f.toUpperCase()}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {/* Looks List */}
      <ScrollView
        style={styles.looksList}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      >
        {data.saved_looks.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>No Looks Saved Yet</Text>
            <Text style={styles.emptyDesc}>
              Build and save outfits in Outfit Studio to curate your personal fashion lookbook.
            </Text>
          </View>
        ) : (
          data.saved_looks.map((look) => (
            <SavedLookCard
              key={look.id}
              look={look}
              onPressLook={onPressLook}
              onDuplicate={onDuplicateLook}
              onDelete={onDeleteLook}
              currency={currency}
            />
          ))
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f9fafb",
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
    backgroundColor: "#ffffff",
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
    color: "#111111",
  },
  subtitle: {
    fontSize: 12,
    color: "#6b7280",
    marginTop: 2,
  },
  filterBar: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#eeeeee",
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: "#f3f4f6",
  },
  activeFilterChip: {
    backgroundColor: "#111111",
  },
  filterText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#6b7280",
    letterSpacing: 0.5,
  },
  activeFilterText: {
    color: "#ffffff",
  },
  looksList: {
    flex: 1,
  },
  listContent: {
    padding: 16,
    paddingBottom: 32,
  },
  emptyState: {
    paddingVertical: 48,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#374151",
    marginBottom: 6,
  },
  emptyDesc: {
    fontSize: 13,
    color: "#6b7280",
    textAlign: "center",
    maxWidth: 260,
    lineHeight: 18,
  },
});
