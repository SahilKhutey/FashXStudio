import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { SavedFashionContract } from "../types";

interface SavedFashionCardProps {
  fashion: SavedFashionContract;
  onOpen?: (contentId: string) => void;
  onRemove?: (id: string) => void;
  testID?: string;
}

export const SavedFashionCard: React.FC<SavedFashionCardProps> = ({
  fashion,
  onOpen,
  onRemove,
  testID = `saved-fashion-card-${fashion.id}`,
}) => {
  return (
    <View testID={testID} style={styles.card}>
      <View style={styles.imageCol}>
        {fashion.image_url ? (
          <Image source={{ uri: fashion.image_url }} style={styles.image} />
        ) : (
          <View style={styles.imagePlaceholder}>
            <Text style={styles.placeholderText}>EDITORIAL</Text>
          </View>
        )}
      </View>

      <View style={styles.contentCol}>
        <View style={styles.badgeRow}>
          <View style={styles.typeBadge}>
            <Text style={styles.typeBadgeText}>
              {fashion.content_type.toUpperCase()}
            </Text>
          </View>
          {onRemove && (
            <TouchableOpacity
              testID={`remove-fashion-${fashion.id}`}
              onPress={() => onRemove(fashion.id)}
              accessibilityRole="button"
              accessibilityLabel={`Remove ${fashion.title}`}
            >
              <Text style={styles.removeText}>✕</Text>
            </TouchableOpacity>
          )}
        </View>

        <Text style={styles.title} numberOfLines={2}>
          {fashion.title}
        </Text>

        {fashion.author_or_brand && (
          <Text style={styles.author}>{fashion.author_or_brand}</Text>
        )}

        <TouchableOpacity
          testID={`read-fashion-${fashion.id}`}
          style={styles.openBtn}
          onPress={() => onOpen && onOpen(fashion.content_id)}
          accessibilityRole="button"
          accessibilityLabel={`Read ${fashion.title}`}
        >
          <Text style={styles.openBtnText}>Open</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    overflow: "hidden",
    marginBottom: 12,
  },
  imageCol: {
    width: 100,
    backgroundColor: "#F2F2F7",
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
    fontSize: 10,
    fontWeight: "700",
    color: "#8E8E93",
  },
  contentCol: {
    flex: 1,
    padding: 12,
    justifyContent: "space-between",
  },
  badgeRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
  },
  typeBadge: {
    backgroundColor: "#F2F2F7",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  typeBadgeText: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.5,
  },
  removeText: {
    color: "#C7C7CC",
    fontSize: 14,
    fontWeight: "700",
  },
  title: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1C1C1E",
    lineHeight: 18,
    marginBottom: 4,
  },
  author: {
    fontSize: 12,
    color: "#8E8E93",
    marginBottom: 8,
  },
  openBtn: {
    alignSelf: "flex-start",
    backgroundColor: "#1C1C1E",
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 4,
  },
  openBtnText: {
    color: "#FFFFFF",
    fontSize: 11,
    fontWeight: "600",
  },
});
