/**
 * OrderCard Component — Phase 07 (Section 7.48 & 7.49).
 *
 * Renders individual customer order in history list with status pill,
 * item previews, placed date, total amount, and view detail CTA.
 */

import React from "react";
import { Image, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { Order, OrderStatus } from "../types";

export interface OrderCardProps {
  order: Order;
  onViewOrderDetail: (orderId: string) => void;
}

export const OrderCard: React.FC<OrderCardProps> = ({ order, onViewOrderDetail }) => {
  const getStatusColor = (status: OrderStatus) => {
    switch (status) {
      case "delivered":
        return defaultDesignTokens.status.success;
      case "shipped":
      case "out_for_delivery":
        return defaultDesignTokens.brand.accent;
      case "cancelled":
      case "returned":
      case "refunded":
        return defaultDesignTokens.status.error;
      case "placed":
      case "processing":
      default:
        return defaultDesignTokens.status.warning;
    }
  };

  const statusColor = getStatusColor(order.status);
  const formattedDate = new Date(order.placedAt).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View>
          <Text style={styles.orderNumber}>{order.orderNumber}</Text>
          <Text style={styles.date}>{formattedDate}</Text>
        </View>

        <View style={[styles.statusBadge, { borderColor: statusColor }]}>
          <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
          <Text style={[styles.statusText, { color: statusColor }]}>
            {order.status.replace("_", " ").toUpperCase()}
          </Text>
        </View>
      </View>

      {/* Item thumbnails */}
      <View style={styles.thumbnailsRow}>
        {order.items.slice(0, 4).map((item) => (
          <Image
            key={item.productId}
            source={{ uri: item.mediaUri }}
            style={styles.thumbnail}
            resizeMode="cover"
          />
        ))}
        {order.items.length > 4 ? (
          <View style={styles.moreThumbnail}>
            <Text style={styles.moreText}>+{order.items.length - 4}</Text>
          </View>
        ) : null}
      </View>

      <View style={styles.footer}>
        <View>
          <Text style={styles.totalLabel}>{order.items.length} items</Text>
          <Text style={styles.totalValue}>
            {order.priceSummary.currencySymbol}
            {order.priceSummary.total.toLocaleString()}
          </Text>
        </View>

        <TouchableOpacity
          accessibilityLabel={`View details for order ${order.orderNumber}`}
          style={styles.actionButton}
          onPress={() => onViewOrderDetail(order.orderId)}
        >
          <Text style={styles.actionButtonText}>View Order →</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
    borderWidth: 1,
    borderColor: defaultDesignTokens.neutral.neutral200,
    gap: 12,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  orderNumber: {
    fontSize: 14,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
  },
  date: {
    fontSize: 12,
    color: defaultDesignTokens.neutral.neutral500,
  },
  statusBadge: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    gap: 6,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.3,
  },
  thumbnailsRow: {
    flexDirection: "row",
    gap: 8,
    marginVertical: 4,
  },
  thumbnail: {
    width: 48,
    height: 64,
    borderRadius: 6,
    backgroundColor: defaultDesignTokens.neutral.neutral100,
  },
  moreThumbnail: {
    width: 48,
    height: 64,
    borderRadius: 6,
    backgroundColor: defaultDesignTokens.neutral.neutral200,
    justifyContent: "center",
    alignItems: "center",
  },
  moreText: {
    fontSize: 12,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral600,
  },
  footer: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: defaultDesignTokens.neutral.neutral100,
  },
  totalLabel: {
    fontSize: 12,
    color: defaultDesignTokens.neutral.neutral500,
  },
  totalValue: {
    fontSize: 16,
    fontWeight: "800",
    color: defaultDesignTokens.neutral.neutral900,
  },
  actionButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    backgroundColor: defaultDesignTokens.neutral.neutral100,
  },
  actionButtonText: {
    fontSize: 13,
    fontWeight: "600",
    color: defaultDesignTokens.brand.primary,
  },
});
