import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { SavedLooksTemplateSpecContract } from "../types";
import { SavedLookCard } from "../components/SavedLookCard";

interface SavedLooksTemplateProps {
  data: SavedLooksTemplateSpecContract;
  onSelectCollection?: (collectionId: string | null) => void;
  onOpenLook?: (lookId: string) => void;
  onEditLook?: (lookId: string) => void;
  onRemoveLook?: (lookId: string) => void;
  onExploreLooks?: () => void;
  onCreateOutfit?: () => void;
  testID?: string;
}

export const SavedLooksTemplate: React.FC<SavedLooksTemplateProps> = ({
  data,
  onSelectCollection,
  onOpenLook,
  onEditLook,
  onRemoveLook,
  onExploreLooks,
  onCreateOutfit,
  testID = "saved-looks-pr04",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Saved Looks ({data.total_count})</Text>

        {/* Collections filter */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.collectionsBar}>
          <TouchableOpacity
            testID="collection-chip-all"
            style={[styles.colChip, !data.active_collection && styles.activeColChip]}
            onPress={() => onSelectCollection && onSelectCollection(null)}
          >
            <Text style={[styles.colText, !data.active_collection && styles.activeColText]}>
              All Collections
            </Text>
          </TouchableOpacity>
          {data.collections.map((col) => (
            <TouchableOpacity
              key={col.id}
              testID={`collection-chip-${col.id}`}
              style={[
                styles.colChip,
                data.active_collection === col.id && styles.activeColChip,
              ]}
              onPress={() => onSelectCollection && onSelectCollection(col.id)}
            >
              <Text
                style={[
                  styles.colText,
                  data.active_collection === col.id && styles.activeColText,
                ]}
              >
                {col.name} ({col.item_count})
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {data.items.length === 0 ? (
        <View testID="empty-saved-looks" style={styles.emptyState}>
          <Text style={styles.emptyTitle}>No saved looks yet.</Text>
          <Text style={styles.emptySubtitle}>
            Explore looks or create an outfit to start your collection.
          </Text>
          <View style={styles.emptyActions}>
            <TouchableOpacity
              testID="explore-looks-button"
              style={styles.primaryBtn}
              onPress={onExploreLooks}
              accessibilityRole="button"
              accessibilityLabel="Explore Looks"
            >
              <Text style={styles.primaryBtnText}>Explore Looks</Text>
            </TouchableOpacity>
            <TouchableOpacity
              testID="create-outfit-button"
              style={styles.secondaryBtn}
              onPress={onCreateOutfit}
              accessibilityRole="button"
              accessibilityLabel="Create Outfit"
            >
              <Text style={styles.secondaryBtnText}>Create Outfit</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.list}>
          {data.items.map((look) => (
            <SavedLookCard
              key={look.id}
              look={look}
              onOpen={onOpenLook}
              onEdit={onEditLook}
              onRemove={onRemoveLook}
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
  collectionsBar: {
    flexDirection: "row",
  },
  colChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: "#F2F2F7",
    marginRight: 8,
  },
  activeColChip: {
    backgroundColor: "#1C1C1E",
  },
  colText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#636366",
  },
  activeColText: {
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
    marginBottom: 6,
  },
  emptySubtitle: {
    fontSize: 13,
    color: "#636366",
    textAlign: "center",
    marginBottom: 20,
  },
  emptyActions: {
    flexDirection: "row",
    gap: 12,
  },
  primaryBtn: {
    backgroundColor: "#1C1C1E",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
  },
  primaryBtnText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "600",
  },
  secondaryBtn: {
    borderWidth: 1,
    borderColor: "#C7C7CC",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
  },
  secondaryBtnText: {
    color: "#1C1C1E",
    fontSize: 13,
    fontWeight: "600",
  },
});
