import React, { useState } from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import {
  MeasurementUnit,
  ProductSizeChartResponse,
  SizeChartUnavailableResponse,
} from "../types/sizeChart";

export interface ProductSizeChartProps {
  chart: ProductSizeChartResponse | SizeChartUnavailableResponse | null;
  onUnitChange?: (unit: MeasurementUnit) => void;
}

export function ProductSizeChart({ chart, onUnitChange }: ProductSizeChartProps) {
  const [activeUnit, setActiveUnit] = useState<MeasurementUnit>(
    chart && "display_unit" in chart ? chart.display_unit : "CM"
  );

  const handleUnitToggle = (unit: MeasurementUnit) => {
    setActiveUnit(unit);
    onUnitChange?.(unit);
  };

  // Fail-closed empty / unavailable state
  if (!chart || "status" in chart && chart.status === "UNAVAILABLE" || !("rows" in chart) || chart.rows.length === 0) {
    return (
      <View style={styles.container} accessible={true} accessibilityRole="text">
        <Text style={styles.heading}>Size and dimensions</Text>
        <View style={styles.unavailableCard}>
          <Text style={styles.unavailableTitle}>Size chart not available</Text>
          <Text style={styles.unavailableMessage}>
            The merchant has not provided a verified size chart for this product. FashXStudio does not infer, generate, or approximate missing dimensions.
          </Text>
        </View>
        <Text style={styles.disclaimer}>
          Virtual try-on simulates appearance only. It does not measure or verify physical fit.
        </Text>
      </View>
    );
  }

  const {
    size_system,
    measurement_basis,
    version,
    is_stale,
    provenance,
    rows,
    last_verified_at,
  } = chart;

  const basisLabel =
    measurement_basis === "BODY" ? "Body measurements" : "Garment measurements";

  // Collect all unique measurement field codes across all rows to form columns
  const fieldOrder: { code: string; label: string }[] = [];
  const seenFields = new Set<string>();

  for (const row of rows) {
    for (const m of row.measurements) {
      if (!seenFields.has(m.field_code)) {
        seenFields.add(m.field_code);
        fieldOrder.push({ code: m.field_code, label: m.display_name });
      }
    }
  }

  const verifiedDateStr = last_verified_at
    ? new Date(last_verified_at).toLocaleDateString()
    : "Recently";

  return (
    <View style={styles.container} accessible={true} accessibilityRole="summary">
      {/* Header with Title and Unit Selector */}
      <View style={styles.headerRow}>
        <View>
          <Text style={styles.heading}>Size and dimensions</Text>
          <Text style={styles.caption}>
            {basisLabel} · System: {size_system.display_name} (v{version})
          </Text>
        </View>

        <View style={styles.unitToggle}>
          <TouchableOpacity
            style={[styles.unitButton, activeUnit === "CM" && styles.activeUnitButton]}
            onPress={() => handleUnitToggle("CM")}
            accessibilityRole="button"
            accessibilityLabel="Show measurements in centimeters"
          >
            <Text
              style={[styles.unitButtonText, activeUnit === "CM" && styles.activeUnitButtonText]}
            >
              CM
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.unitButton, activeUnit === "INCH" && styles.activeUnitButton]}
            onPress={() => handleUnitToggle("INCH")}
            accessibilityRole="button"
            accessibilityLabel="Show measurements in inches"
          >
            <Text
              style={[styles.unitButtonText, activeUnit === "INCH" && styles.activeUnitButtonText]}
            >
              IN
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Sizing system mapping warning if unmapped */}
      {size_system.mapping_status === "UNMAPPED" && (
        <View style={styles.infoBanner}>
          <Text style={styles.infoBannerText}>
            Showing merchant's native {size_system.code} sizes. Direct conversion to your preferred system is not verified by this merchant.
          </Text>
        </View>
      )}

      {/* Dynamic Measurements Table */}
      <ScrollView horizontal showsHorizontalScrollIndicator={true} style={styles.tableScroll}>
        <View style={styles.table}>
          <View style={[styles.row, styles.headerTableRow]}>
            <Text style={[styles.cell, styles.headerCell, styles.sizeColumn]}>Size</Text>
            {fieldOrder.map((f) => (
              <Text key={f.code} style={[styles.cell, styles.headerCell]}>
                {f.label}
              </Text>
            ))}
          </View>

          {rows.map((row) => {
            const measMap = new Map(row.measurements.map((m) => [m.field_code, m.value]));
            return (
              <View key={row.merchant_size} style={styles.row}>
                <Text style={[styles.cell, styles.sizeCell, styles.sizeColumn]}>
                  {row.merchant_size}
                  {row.mapped_size ? ` (${row.mapped_size})` : ""}
                </Text>
                {fieldOrder.map((f) => {
                  const val = measMap.get(f.code);
                  return (
                    <Text key={f.code} style={styles.cell}>
                      {val !== undefined && val !== null ? `${val}` : "—"}
                    </Text>
                  );
                })}
              </View>
            );
          })}
        </View>
      </ScrollView>

      {/* Provenance & Stale warnings */}
      <View style={styles.metaRow}>
        <Text style={styles.metaText}>
          Source: {provenance.source_id || "Merchant API"} · Verified: {verifiedDateStr}
        </Text>
        {is_stale && (
          <View style={styles.staleBadge}>
            <Text style={styles.staleBadgeText}>UNVERIFIED / STALE</Text>
          </View>
        )}
      </View>

      {/* Mandatory Physical Fit Disclaimer */}
      <Text style={styles.disclaimer}>
        Size charts describe physical garment dimensions provided directly by the merchant. Visual try-on simulates visual drape only and does not establish verified physical fit.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 16,
    marginVertical: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 8,
  },
  heading: {
    fontSize: 17,
    fontWeight: "700",
    color: "#111827",
  },
  caption: {
    fontSize: 12,
    color: "#6B7280",
    marginTop: 2,
  },
  unitToggle: {
    flexDirection: "row",
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    overflow: "hidden",
  },
  unitButton: {
    paddingVertical: 4,
    paddingHorizontal: 8,
    backgroundColor: "#F9FAFB",
  },
  activeUnitButton: {
    backgroundColor: "#0F766E",
  },
  unitButtonText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#4B5563",
  },
  activeUnitButtonText: {
    color: "#FFFFFF",
  },
  infoBanner: {
    backgroundColor: "#EFF6FF",
    borderRadius: 6,
    padding: 8,
    marginVertical: 8,
    borderLeftWidth: 3,
    borderLeftColor: "#3B82F6",
  },
  infoBannerText: {
    fontSize: 11,
    color: "#1E40AF",
  },
  tableScroll: {
    marginTop: 8,
    marginBottom: 12,
  },
  table: {
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 8,
    overflow: "hidden",
  },
  row: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
    alignItems: "center",
  },
  headerTableRow: {
    backgroundColor: "#F9FAFB",
    borderBottomWidth: 1.5,
    borderBottomColor: "#E5E7EB",
  },
  cell: {
    minWidth: 70,
    paddingVertical: 10,
    paddingHorizontal: 12,
    fontSize: 13,
    color: "#374151",
    textAlign: "center",
  },
  sizeColumn: {
    minWidth: 80,
    textAlign: "left",
    fontWeight: "600",
  },
  headerCell: {
    fontWeight: "700",
    color: "#111827",
    fontSize: 12,
  },
  sizeCell: {
    color: "#111827",
    backgroundColor: "#FAF5FF",
  },
  metaRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  metaText: {
    fontSize: 11,
    color: "#9CA3AF",
  },
  staleBadge: {
    backgroundColor: "#FEF3C7",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  staleBadgeText: {
    fontSize: 9,
    fontWeight: "700",
    color: "#B45309",
  },
  disclaimer: {
    fontSize: 11,
    color: "#6B7280",
    fontStyle: "italic",
    lineHeight: 16,
  },
  unavailableCard: {
    backgroundColor: "#F9FAFB",
    borderRadius: 8,
    padding: 12,
    marginVertical: 8,
    borderLeftWidth: 3,
    borderLeftColor: "#9CA3AF",
  },
  unavailableTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#374151",
    marginBottom: 4,
  },
  unavailableMessage: {
    fontSize: 12,
    color: "#6B7280",
    lineHeight: 16,
  },
});
