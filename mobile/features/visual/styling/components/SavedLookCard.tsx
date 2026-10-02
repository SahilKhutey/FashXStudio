import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { SavedLookContract } from "../types";

interface SavedLookCardProps {
  look: SavedLookContract;
  onPressLook?: (lookId: string) => void;
  onDuplicate?: (lookId: string) => void;
  onDelete?: (lookId: string) => void;
  currency?: string;
  testID?: string;
}

export const SavedLookCard: React.FC<SavedLookCardProps> = ({
  look,
  onPressLook,
  onDuplicate,
  onDelete,
  currency = "INR",
  testID = `saved-look-${look.id}`,
}) => {
  const totalPrice = look.items.reduce((acc, it) => acc + it.price, 0);

  return (
    <View testID={testID} style={styles.cardContainer}>
      <TouchableOpacity
        activeOpacity={0.85}
        onPress={() => onPressLook?.(look.id)}
        style={styles.cardHeaderArea}
      >
        {/* Thumbnails row / collage */}
        <View style={styles.thumbnailsRow}>
          {look.items.slice(0, 4).map((item, idx) => (
            <Image
              key={`${item.product_id}-${idx}`}
              source={{ uri: item.image_uri }}
              style={styles.thumbnail}
              resizeMode="cover"
            />
          ))}
          {look.items.length === 0 && (
            <View style={styles.emptyThumbnail}>
              <Text style={styles.emptyThumbText}>Empty Look</Text>
            </View>
          )}
        </View>

        {/* Metadata */}
        <View style={styles.metadata}>
          <View style={styles.metaRow}>
            <Text style={styles.styleTag}>{look.style_name.toUpperCase()}</Text>
            {look.collection_tag && (
              <Text style={styles.collectionBadge}>#{look.collection_tag}</Text>
            )}
          </View>
          <Text style={styles.lookName}>{look.name}</Text>
          <Text style={styles.itemsCount}>
            {look.items.length} items • {currency === "INR" ? "₹" : "$"}
            {totalPrice.toLocaleString()}
          </Text>
          <Text style={styles.dateText}>Created {look.created_at}</Text>
        </View>
      </TouchableOpacity>

      {/* Action Buttons */}
      <View style={styles.actionsRow}>
        <TouchableOpacity
          testID={`${testID}-open`}
          style={styles.openButton}
          onPress={() => onPressLook?.(look.id)}
        >
          <Text style={styles.openButtonText}>Open in Builder</Text>
        </TouchableOpacity>

        {onDuplicate && (
          <TouchableOpacity
            testID={`${testID}-duplicate`}
            style={styles.secondaryAction}
            onPress={() => onDuplicate(look.id)}
          >
            <Text style={styles.secondaryActionText}>Clone</Text>
          </TouchableOpacity>
        )}

        {onDelete && (
          <TouchableOpacity
            testID={`${testID}-delete`}
            style={[styles.secondaryAction, styles.deleteAction]}
            onPress={() => onDelete(look.id)}
          >
            <Text style={styles.deleteActionText}>✕</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  cardContainer: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    marginBottom: 16,
    overflow: "hidden",
  },
  cardHeaderArea: {
    padding: 12,
  },
  thumbnailsRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 12,
  },
  thumbnail: {
    flex: 1,
    height: 100,
    borderRadius: 6,
    backgroundColor: "#f3f4f6",
  },
  emptyThumbnail: {
    flex: 1,
    height: 100,
    borderRadius: 6,
    backgroundColor: "#f9fafb",
    alignItems: "center",
    justifyContent: "center",
  },
  emptyThumbText: {
    color: "#9ca3af",
    fontSize: 12,
  },
  metadata: {
    gap: 4,
  },
  metaRow: {
    flexDirection: "row",
    gap: 6,
    alignItems: "center",
  },
  styleTag: {
    fontSize: 11,
    fontWeight: "700",
    color: "#6b7280",
    letterSpacing: 0.5,
  },
  collectionBadge: {
    fontSize: 11,
    color: "#3b82f6",
    fontWeight: "600",
  },
  lookName: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111111",
  },
  itemsCount: {
    fontSize: 13,
    color: "#374151",
    fontWeight: "600",
  },
  dateText: {
    fontSize: 11,
    color: "#9ca3af",
  },
  actionsRow: {
    flexDirection: "row",
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: "#f3f4f6",
    gap: 8,
    alignItems: "center",
  },
  openButton: {
    flex: 1,
    backgroundColor: "#111111",
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: "center",
  },
  openButtonText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "600",
  },
  secondaryAction: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    backgroundColor: "#f3f4f6",
  },
  secondaryActionText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#374151",
  },
  deleteAction: {
    backgroundColor: "#fee2e2",
  },
  deleteActionText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#b91c1c",
  },
});
