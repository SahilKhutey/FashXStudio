import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";

export type SizeRow = {
  size: string;
  chest?: string | number;
  waist?: string | number;
  hip?: string | number;
  length?: string | number;
  shoulder?: string | number;
};

export interface ProductSizeChartProps {
  rows: SizeRow[];
  basis: "BODY" | "GARMENT";
  unit: "CM" | "INCH";
  merchantName: string;
  verified: boolean;
  isStale?: boolean;
}

/**
 * ProductSizeChart Component (Phase 07.8 - Task 7.8.2)
 *
 * Displays merchant-sourced size tables with explicit basis and unit provenance.
 * Preserves the invariant that merchant sizing data is independent of visual try-on.
 */
export function ProductSizeChart({
  rows,
  basis,
  unit,
  merchantName,
  verified,
  isStale = false,
}: ProductSizeChartProps) {
  const basisLabel = basis === "BODY" ? "Body measurements" : "Garment measurements";

  if (!rows || rows.length === 0) {
    return (
      <View style={styles.container} accessible={true} accessibilityRole="text">
        <Text style={styles.heading}>Merchant size chart</Text>
        <Text style={styles.source}>Source: {merchantName}</Text>
        <Text style={styles.emptyMessage}>
          The merchant has not provided a verified size chart for this product.
        </Text>
        <Text style={styles.disclaimer}>
          Virtual try-on does not verify physical garment fit or dimensions.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container} accessible={true} accessibilityRole="summary">
      <View style={styles.headerRow}>
        <Text style={styles.heading}>Merchant size chart</Text>
        <View style={[styles.badge, verified ? styles.verifiedBadge : styles.unverifiedBadge]}>
          <Text style={[styles.badgeText, verified ? styles.verifiedText : styles.unverifiedText]}>
            {verified ? "VERIFIED SOURCE" : "UNVERIFIED"}
          </Text>
        </View>
      </View>

      <Text style={styles.source}>
        Source: {merchantName} {" · "} {verified ? "Official merchant data" : "Pending verification"}
      </Text>
      <Text style={styles.caption}>
        {basisLabel} · Units: {unit}
      </Text>

      <ScrollView horizontal showsHorizontalScrollIndicator={true} style={styles.tableScroll}>
        <View style={styles.table}>
          <View style={[styles.row, styles.headerTableRow]}>
            <Text style={[styles.cell, styles.headerCell]}>Size</Text>
            <Text style={[styles.cell, styles.headerCell]}>Chest</Text>
            <Text style={[styles.cell, styles.headerCell]}>Waist</Text>
            <Text style={[styles.cell, styles.headerCell]}>Hip</Text>
            <Text style={[styles.cell, styles.headerCell]}>Length</Text>
            <Text style={[styles.cell, styles.headerCell]}>Shoulder</Text>
          </View>
          {rows.map((row) => (
            <View key={row.size} style={styles.row}>
              <Text style={[styles.cell, styles.sizeCell]}>{row.size}</Text>
              <Text style={styles.cell}>{row.chest !== undefined && row.chest !== null ? `${row.chest}` : "—"}</Text>
              <Text style={styles.cell}>{row.waist !== undefined && row.waist !== null ? `${row.waist}` : "—"}</Text>
              <Text style={styles.cell}>{row.hip !== undefined && row.hip !== null ? `${row.hip}` : "—"}</Text>
              <Text style={styles.cell}>{row.length !== undefined && row.length !== null ? `${row.length}` : "—"}</Text>
              <Text style={styles.cell}>{row.shoulder !== undefined && row.shoulder !== null ? `${row.shoulder}` : "—"}</Text>
            </View>
          ))}
        </View>
      </ScrollView>

      {isStale && (
        <Text style={styles.staleWarning}>
          ⚠️ This size information has not been verified against the latest merchant source.
        </Text>
      )}

      <Text style={styles.disclaimer}>
        Size charts are supplied directly by the merchant. Virtual try-on images do not verify physical fit.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E4E7EC",
    gap: 8,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  heading: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1D2939",
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  verifiedBadge: {
    backgroundColor: "#ECFDF3",
  },
  unverifiedBadge: {
    backgroundColor: "#FEF3F2",
  },
  badgeText: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  verifiedText: {
    color: "#027A48",
  },
  unverifiedText: {
    color: "#B42318",
  },
  source: {
    fontSize: 12,
    color: "#667085",
  },
  caption: {
    fontSize: 13,
    fontWeight: "500",
    color: "#344054",
  },
  tableScroll: {
    marginTop: 4,
    marginBottom: 4,
  },
  table: {
    minWidth: 420,
    borderWidth: 1,
    borderColor: "#EAECF0",
    borderRadius: 8,
    overflow: "hidden",
  },
  row: {
    flexDirection: "row",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#EAECF0",
    alignItems: "center",
  },
  headerTableRow: {
    backgroundColor: "#F9FAFB",
  },
  cell: {
    width: 70,
    paddingVertical: 8,
    paddingHorizontal: 6,
    fontSize: 12,
    textAlign: "center",
    color: "#344054",
  },
  headerCell: {
    fontWeight: "700",
    color: "#475467",
  },
  sizeCell: {
    fontWeight: "700",
    color: "#1D2939",
  },
  staleWarning: {
    fontSize: 12,
    color: "#B54708",
    backgroundColor: "#FFFAEB",
    padding: 8,
    borderRadius: 6,
  },
  emptyMessage: {
    fontSize: 13,
    color: "#667085",
    paddingVertical: 12,
  },
  disclaimer: {
    fontSize: 11,
    lineHeight: 15,
    color: "#98A2B3",
    marginTop: 4,
  },
});
