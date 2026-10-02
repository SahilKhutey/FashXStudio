import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { SavedLookContract } from "../types";

interface SavedLookCardProps {
  look: SavedLookContract;
  onOpen?: (lookId: string) => void;
  onEdit?: (lookId: string) => void;
  onShare?: (lookId: string) => void;
  onRemove?: (lookId: string) => void;
  testID?: string;
}

export const SavedLookCard: React.FC<SavedLookCardProps> = ({
  look,
  onOpen,
  onEdit,
  onShare,
  onRemove,
  testID = `saved-look-card-${look.id}`,
}) => {
  return (
    <View testID={testID} style={styles.card}>
      <View style={styles.imageContainer}>
        {look.image_url ? (
          <Image source={{ uri: look.image_url }} style={styles.image} />
        ) : (
          <View style={styles.imagePlaceholder}>
            <Text style={styles.placeholderText}>OUTFIT LOOK</Text>
          </View>
        )}
        <View style={styles.itemsBadge}>
          <Text style={styles.itemsBadgeText}>{look.items_count} PIECES</Text>
        </View>
      </View>

      <View style={styles.content}>
        <Text style={styles.styleTag}>{look.style}</Text>
        <Text style={styles.title} numberOfLines={2}>
          {look.title}
        </Text>

        <View style={styles.actionRow}>
          <TouchableOpacity
            testID={`open-look-${look.id}`}
            style={styles.primaryBtn}
            onPress={() => onOpen && onOpen(look.look_id)}
            accessibilityRole="button"
            accessibilityLabel={`Open ${look.title}`}
          >
            <Text style={styles.primaryBtnText}>Open</Text>
          </TouchableOpacity>

          <TouchableOpacity
            testID={`edit-look-${look.id}`}
            style={styles.secondaryBtn}
            onPress={() => onEdit && onEdit(look.look_id)}
            accessibilityRole="button"
            accessibilityLabel={`Edit ${look.title} in outfit builder`}
          >
            <Text style={styles.secondaryBtnText}>Edit</Text>
          </TouchableOpacity>

          {onRemove && (
            <TouchableOpacity
              testID={`remove-look-${look.id}`}
              style={styles.iconBtn}
              onPress={() => onRemove(look.id)}
              accessibilityRole="button"
              accessibilityLabel={`Remove ${look.title}`}
            >
              <Text style={styles.iconBtnText}>✕</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    overflow: "hidden",
    marginBottom: 12,
  },
  imageContainer: {
    height: 190,
    backgroundColor: "#F2F2F7",
    position: "relative",
  },
  image: {
    width: "100%",
    height: "100%",
    resizeMode: "cover",
  },
  imagePlaceholder: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  placeholderText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#8E8E93",
  },
  itemsBadge: {
    position: "absolute",
    bottom: 8,
    left: 8,
    backgroundColor: "rgba(0, 0, 0, 0.7)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  itemsBadgeText: {
    color: "#FFFFFF",
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  content: {
    padding: 12,
  },
  styleTag: {
    fontSize: 11,
    fontWeight: "600",
    color: "#5856D6",
    textTransform: "uppercase",
    marginBottom: 4,
  },
  title: {
    fontSize: 15,
    fontWeight: "600",
    color: "#1C1C1E",
    marginBottom: 12,
  },
  actionRow: {
    flexDirection: "row",
    gap: 8,
    alignItems: "center",
  },
  primaryBtn: {
    flex: 1,
    backgroundColor: "#1C1C1E",
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: "center",
  },
  primaryBtnText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "600",
  },
  secondaryBtn: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: "#C7C7CC",
    borderRadius: 6,
    alignItems: "center",
  },
  secondaryBtnText: {
    color: "#1C1C1E",
    fontSize: 12,
    fontWeight: "600",
  },
  iconBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#E5E5EA",
  },
  iconBtnText: {
    color: "#8E8E93",
    fontSize: 12,
    fontWeight: "600",
  },
});
