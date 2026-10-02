import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { SavedProductContract } from "../types";

interface SavedProductCardProps {
  product: SavedProductContract;
  onView?: (productId: string) => void;
  onRemove?: (productId: string) => void;
  testID?: string;
}

export const SavedProductCard: React.FC<SavedProductCardProps> = ({
  product,
  onView,
  onRemove,
  testID = `saved-product-card-${product.id}`,
}) => {
  const isAvailable = product.availability !== "out_of_stock";

  return (
    <View testID={testID} style={styles.card}>
      <View style={styles.imageContainer}>
        {product.image_url ? (
          <Image source={{ uri: product.image_url }} style={styles.image} />
        ) : (
          <View style={styles.imagePlaceholder}>
            <Text style={styles.placeholderText}>GARMENT</Text>
          </View>
        )}
        <View style={styles.savedBadge} accessibilityLabel="Saved in Products">
          <Text style={styles.savedBadgeText}>♥ SAVED</Text>
        </View>
      </View>

      <View style={styles.info}>
        <Text style={styles.brand}>{product.brand}</Text>
        <Text style={styles.name} numberOfLines={2}>
          {product.name}
        </Text>
        <Text style={styles.price}>
          {product.currency} ${product.price.toFixed(2)}
        </Text>

        <View style={styles.statusRow}>
          <View
            style={[
              styles.availabilityBadge,
              isAvailable ? styles.availableBadge : styles.unavailableBadge,
            ]}
          >
            <Text
              style={[
                styles.availabilityText,
                isAvailable ? styles.availableText : styles.unavailableText,
              ]}
            >
              {product.availability === "in_stock"
                ? "In Stock"
                : product.availability === "low_stock"
                ? "Low Stock"
                : "Out of Stock"}
            </Text>
          </View>
          <Text style={styles.savedLabel}>{product.saved_state_label}</Text>
        </View>

        <View style={styles.actions}>
          <TouchableOpacity
            testID={`view-btn-${product.id}`}
            style={styles.viewButton}
            onPress={() => onView && onView(product.product_id)}
            accessibilityRole="button"
            accessibilityLabel={`View ${product.name}`}
          >
            <Text style={styles.viewButtonText}>View Details</Text>
          </TouchableOpacity>

          {onRemove && (
            <TouchableOpacity
              testID={`remove-btn-${product.id}`}
              style={styles.removeButton}
              onPress={() => onRemove(product.id)}
              accessibilityRole="button"
              accessibilityLabel={`Remove ${product.name} from saved items`}
            >
              <Text style={styles.removeButtonText}>Remove</Text>
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
    height: 180,
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
  savedBadge: {
    position: "absolute",
    top: 8,
    right: 8,
    backgroundColor: "rgba(28, 28, 30, 0.85)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  savedBadgeText: {
    color: "#FFFFFF",
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  info: {
    padding: 12,
  },
  brand: {
    fontSize: 11,
    fontWeight: "600",
    color: "#8E8E93",
    textTransform: "uppercase",
    marginBottom: 2,
  },
  name: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1C1C1E",
    marginBottom: 4,
  },
  price: {
    fontSize: 14,
    fontWeight: "700",
    color: "#1C1C1E",
    marginBottom: 8,
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  availabilityBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  availableBadge: {
    backgroundColor: "#E8F8EE",
  },
  unavailableBadge: {
    backgroundColor: "#FFF0F0",
  },
  availabilityText: {
    fontSize: 10,
    fontWeight: "600",
  },
  availableText: {
    color: "#1B873F",
  },
  unavailableText: {
    color: "#D70015",
  },
  savedLabel: {
    fontSize: 10,
    color: "#636366",
  },
  actions: {
    flexDirection: "row",
    gap: 8,
  },
  viewButton: {
    flex: 1,
    backgroundColor: "#1C1C1E",
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: "center",
  },
  viewButtonText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "600",
  },
  removeButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    borderRadius: 6,
    alignItems: "center",
  },
  removeButtonText: {
    color: "#8E8E93",
    fontSize: 12,
    fontWeight: "500",
  },
});
