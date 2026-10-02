import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { RegionContract } from "../types";

interface RegionSummaryPanelProps {
  region: RegionContract;
  onExploreRegion?: (regionId: string) => void;
  onClose?: () => void;
  testID?: string;
}

export const RegionSummaryPanel: React.FC<RegionSummaryPanelProps> = ({
  region,
  onExploreRegion,
  onClose,
  testID = "region-summary-panel",
}) => {
  return (
    <View testID={testID} style={styles.container} accessibilityRole="summary">
      <View style={styles.header}>
        <View style={styles.titleArea}>
          <Text style={styles.typeText}>{region.type.toUpperCase()}</Text>
          <Text style={styles.titleText}>{region.name}</Text>
        </View>
        {onClose && (
          <TouchableOpacity
            testID={`${testID}-close`}
            onPress={onClose}
            style={styles.closeBtn}
            accessibilityLabel="Close region summary"
          >
            <Text style={styles.closeBtnText}>✕</Text>
          </TouchableOpacity>
        )}
      </View>

      {region.description && (
        <Text style={styles.description} numberOfLines={2}>
          {region.description}
        </Text>
      )}

      {/* Metrics Grid */}
      <View style={styles.metricsGrid}>
        <View style={styles.metricBox}>
          <Text style={styles.metricNumber}>{region.trends_count}</Text>
          <Text style={styles.metricLabel}>Trends</Text>
        </View>
        <View style={styles.metricDivider} />
        <View style={styles.metricBox}>
          <Text style={styles.metricNumber}>{region.looks_count}</Text>
          <Text style={styles.metricLabel}>Looks</Text>
        </View>
        <View style={styles.metricDivider} />
        <View style={styles.metricBox}>
          <Text style={styles.metricNumber}>{region.products_count}</Text>
          <Text style={styles.metricLabel}>Products</Text>
        </View>
      </View>

      {/* Primary CTA */}
      <TouchableOpacity
        testID={`${testID}-explore-btn`}
        style={styles.exploreBtn}
        onPress={() => onExploreRegion?.(region.id)}
        accessibilityRole="button"
        accessibilityLabel={`Explore complete fashion culture in ${region.name}`}
      >
        <Text style={styles.exploreBtnText}>Explore Region</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#ffffff",
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    shadowColor: "#000000",
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 4,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 6,
  },
  titleArea: {
    flex: 1,
  },
  typeText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#6b7280",
    letterSpacing: 0.8,
  },
  titleText: {
    fontSize: 20,
    fontWeight: "800",
    color: "#111111",
    marginTop: 2,
  },
  closeBtn: {
    padding: 4,
  },
  closeBtnText: {
    fontSize: 16,
    color: "#9ca3af",
  },
  description: {
    fontSize: 12,
    color: "#4b5563",
    lineHeight: 17,
    marginBottom: 12,
  },
  metricsGrid: {
    flexDirection: "row",
    backgroundColor: "#f9fafb",
    borderRadius: 8,
    paddingVertical: 10,
    marginBottom: 14,
    alignItems: "center",
  },
  metricBox: {
    flex: 1,
    alignItems: "center",
  },
  metricDivider: {
    width: 1,
    height: 24,
    backgroundColor: "#e5e7eb",
  },
  metricNumber: {
    fontSize: 16,
    fontWeight: "800",
    color: "#111111",
  },
  metricLabel: {
    fontSize: 10,
    color: "#6b7280",
    fontWeight: "600",
    marginTop: 1,
  },
  exploreBtn: {
    backgroundColor: "#111111",
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: "center",
  },
  exploreBtnText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "700",
  },
});
