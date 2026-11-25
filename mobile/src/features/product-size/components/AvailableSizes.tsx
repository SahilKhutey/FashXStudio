import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { AvailabilityStatus, VariantStockItem } from "../types/sizeChart";

export interface AvailableSizesProps {
  variants: VariantStockItem[];
  selectedSize?: string | null;
  onSelectSize?: (sizeLabel: string) => void;
}

export function AvailableSizes({
  variants,
  selectedSize,
  onSelectSize,
}: AvailableSizesProps) {
  if (!variants || variants.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.emptyText}>Size availability is currently unknown.</Text>
      </View>
    );
  }

  // Deduplicate by size label while taking best availability status
  const sizeMap = new Map<string, VariantStockItem>();
  for (const v of variants) {
    if (!sizeMap.has(v.size_label)) {
      sizeMap.set(v.size_label, v);
    } else {
      const existing = sizeMap.get(v.size_label)!;
      if (
        v.status === "IN_STOCK" ||
        (v.status === "LOW_STOCK" && existing.status !== "IN_STOCK")
      ) {
        sizeMap.set(v.size_label, v);
      }
    }
  }

  const uniqueSizes = Array.from(sizeMap.values());

  const getStatusBadge = (status: AvailabilityStatus, isStale: boolean) => {
    if (isStale) return { text: "UNVERIFIED", style: styles.staleBadge };
    switch (status) {
      case "IN_STOCK":
        return { text: "IN STOCK", style: styles.inStockBadge };
      case "LOW_STOCK":
        return { text: "FEW LEFT", style: styles.lowStockBadge };
      case "OUT_OF_STOCK":
        return { text: "SOLD OUT", style: styles.outOfStockBadge };
      case "PREORDER":
        return { text: "PREORDER", style: styles.preorderBadge };
      default:
        return { text: "AVAILABILITY UNKNOWN", style: styles.unknownBadge };
    }
  };

  return (
    <View style={styles.container} accessible={true} accessibilityRole="radiogroup">
      <Text style={styles.title}>Available sizes</Text>
      <View style={styles.grid}>
        {uniqueSizes.map((item) => {
          const isSelected = selectedSize === item.size_label;
          const isOutOfStock = item.status === "OUT_OF_STOCK";
          const badge = getStatusBadge(item.status, item.is_stale);

          return (
            <TouchableOpacity
              key={item.size_label}
              style={[
                styles.sizePill,
                isSelected && styles.selectedPill,
                isOutOfStock && styles.outOfStockPill,
              ]}
              disabled={isOutOfStock}
              onPress={() => onSelectSize?.(item.size_label)}
              accessibilityRole="radio"
              accessibilityState={{ selected: isSelected, disabled: isOutOfStock }}
              accessibilityLabel={`Size ${item.size_label}, ${badge.text}`}
            >
              <Text
                style={[
                  styles.sizeText,
                  isSelected && styles.selectedText,
                  isOutOfStock && styles.outOfStockText,
                ]}
              >
                {item.size_label}
              </Text>
              <View style={[styles.badge, badge.style]}>
                <Text style={styles.badgeText}>{badge.text}</Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>
      <Text style={styles.disclaimer}>
        Stock availability reflects merchant inventory reports and may change prior to checkout.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 12,
  },
  title: {
    fontSize: 15,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 8,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  sizePill: {
    minWidth: 70,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: "#E5E7EB",
    backgroundColor: "#FFFFFF",
    alignItems: "center",
  },
  selectedPill: {
    borderColor: "#0F766E",
    backgroundColor: "#F0FDFA",
  },
  outOfStockPill: {
    backgroundColor: "#F9FAFB",
    borderColor: "#F3F4F6",
    opacity: 0.6,
  },
  sizeText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1F2937",
    marginBottom: 4,
  },
  selectedText: {
    color: "#0F766E",
    fontWeight: "700",
  },
  outOfStockText: {
    color: "#9CA3AF",
    textDecorationLine: "line-through",
  },
  badge: {
    paddingHorizontal: 5,
    paddingVertical: 2,
    borderRadius: 4,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: "700",
  },
  inStockBadge: {
    backgroundColor: "#DCFCE7",
  },
  lowStockBadge: {
    backgroundColor: "#FEF3C7",
  },
  outOfStockBadge: {
    backgroundColor: "#FEE2E2",
  },
  preorderBadge: {
    backgroundColor: "#E0E7FF",
  },
  unknownBadge: {
    backgroundColor: "#F3F4F6",
  },
  staleBadge: {
    backgroundColor: "#FEF9C3",
  },
  emptyText: {
    fontSize: 13,
    color: "#6B7280",
    fontStyle: "italic",
  },
  disclaimer: {
    marginTop: 8,
    fontSize: 11,
    color: "#6B7280",
  },
});
