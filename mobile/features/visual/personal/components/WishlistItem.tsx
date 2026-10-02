import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { WishlistItemContract } from "../types";

interface WishlistItemProps {
  item: WishlistItemContract;
  onAddToCart?: (productId: string) => void;
  onViewAlternatives?: (altId: string) => void;
  onRemove?: (id: string) => void;
  testID?: string;
}

export const WishlistItem: React.FC<WishlistItemProps> = ({
  item,
  onAddToCart,
  onViewAlternatives,
  onRemove,
  testID = `wishlist-item-${item.id}`,
}) => {
  return (
    <View testID={testID} style={styles.card}>
      <View style={styles.imageCol}>
        {item.image_url ? (
          <Image source={{ uri: item.image_url }} style={styles.image} />
        ) : (
          <View style={styles.imagePlaceholder}>
            <Text style={styles.placeholderText}>WISHLIST</Text>
          </View>
        )}
      </View>

      <View style={styles.infoCol}>
        <View style={styles.topRow}>
          <Text style={styles.brand}>{item.brand}</Text>
          {onRemove && (
            <TouchableOpacity
              testID={`remove-wish-${item.id}`}
              onPress={() => onRemove(item.id)}
              accessibilityRole="button"
              accessibilityLabel={`Remove ${item.name} from wishlist`}
            >
              <Text style={styles.removeText}>✕</Text>
            </TouchableOpacity>
          )}
        </View>

        <Text style={styles.name} numberOfLines={2}>
          {item.name}
        </Text>
        <Text style={styles.price}>
          {item.currency} ${item.price.toFixed(2)}
        </Text>

        {item.availability_notice ? (
          <View testID={`availability-notice-${item.id}`} style={styles.noticeBox}>
            <Text style={styles.noticeText}>{item.availability_notice}</Text>
          </View>
        ) : null}

        <View style={styles.actions}>
          {item.is_available ? (
            <TouchableOpacity
              testID={`add-cart-${item.id}`}
              style={styles.cartBtn}
              onPress={() => onAddToCart && onAddToCart(item.product_id)}
              accessibilityRole="button"
              accessibilityLabel={`Add ${item.name} to cart`}
            >
              <Text style={styles.cartBtnText}>Add to Cart</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              testID={`alt-btn-${item.id}`}
              style={styles.altBtn}
              onPress={() =>
                onViewAlternatives && item.alternative_product_id &&
                onViewAlternatives(item.alternative_product_id)
              }
              accessibilityRole="button"
              accessibilityLabel={`View alternatives for ${item.name}`}
            >
              <Text style={styles.altBtnText}>View Alternatives</Text>
            </TouchableOpacity>
          )}
        </View>
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
    padding: 12,
  },
  imageCol: {
    width: 90,
    height: 110,
    backgroundColor: "#F2F2F7",
    borderRadius: 6,
    overflow: "hidden",
    marginRight: 12,
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
  infoCol: {
    flex: 1,
    justifyContent: "space-between",
  },
  topRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  brand: {
    fontSize: 11,
    fontWeight: "600",
    color: "#8E8E93",
    textTransform: "uppercase",
  },
  removeText: {
    color: "#8E8E93",
    fontSize: 14,
    fontWeight: "600",
  },
  name: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1C1C1E",
    marginVertical: 2,
  },
  price: {
    fontSize: 14,
    fontWeight: "700",
    color: "#1C1C1E",
    marginBottom: 4,
  },
  noticeBox: {
    backgroundColor: "#FFF5F5",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: "#FFD6D6",
    marginBottom: 8,
  },
  noticeText: {
    color: "#D70015",
    fontSize: 11,
    fontWeight: "500",
  },
  actions: {
    marginTop: 4,
  },
  cartBtn: {
    backgroundColor: "#1C1C1E",
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: "center",
  },
  cartBtnText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "600",
  },
  altBtn: {
    backgroundColor: "#F2F2F7",
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: "center",
  },
  altBtnText: {
    color: "#5856D6",
    fontSize: 12,
    fontWeight: "600",
  },
});
