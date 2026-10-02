import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { RegionContract } from "../types";

interface RegionCardProps {
  region: RegionContract;
  onPressRegion?: (regionId: string) => void;
  compact?: boolean;
  testID?: string;
}

export const RegionCard: React.FC<RegionCardProps> = ({
  region,
  onPressRegion,
  compact = false,
  testID = `region-card-${region.id}`,
}) => {
  return (
    <TouchableOpacity
      testID={testID}
      activeOpacity={0.85}
      onPress={() => onPressRegion?.(region.id)}
      style={[styles.card, compact && styles.compactCard]}
      accessibilityRole="button"
      accessibilityLabel={`Explore fashion in ${region.name}, ${region.type}`}
    >
      {region.hero_image_uri && (
        <Image
          source={{ uri: region.hero_image_uri }}
          style={[styles.heroImage, compact && styles.compactImage]}
          resizeMode="cover"
        />
      )}

      <View style={styles.content}>
        <View style={styles.badgeRow}>
          <View style={styles.typeBadge}>
            <Text style={styles.typeBadgeText}>{region.type.toUpperCase()}</Text>
          </View>
          {region.country_code && (
            <Text style={styles.codeText}>{region.country_code}</Text>
          )}
        </View>

        <Text style={styles.title} numberOfLines={1}>
          {region.name}
        </Text>

        {region.description && !compact && (
          <Text style={styles.description} numberOfLines={2}>
            {region.description}
          </Text>
        )}

        <View style={styles.metricsRow}>
          <Text style={styles.metricItem}>
            <Text style={styles.metricVal}>{region.trends_count}</Text> Trends
          </Text>
          <Text style={styles.metricDot}>•</Text>
          <Text style={styles.metricItem}>
            <Text style={styles.metricVal}>{region.products_count}</Text> Products
          </Text>
          <Text style={styles.metricDot}>•</Text>
          <Text style={styles.metricItem}>
            <Text style={styles.metricVal}>{region.looks_count}</Text> Looks
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    overflow: "hidden",
    marginBottom: 14,
  },
  compactCard: {
    width: 170,
    marginBottom: 0,
  },
  heroImage: {
    width: "100%",
    height: 140,
    backgroundColor: "#f3f4f6",
  },
  compactImage: {
    height: 100,
  },
  content: {
    padding: 12,
  },
  badgeRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 6,
  },
  typeBadge: {
    backgroundColor: "#f3f4f6",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  typeBadgeText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#4b5563",
    letterSpacing: 0.5,
  },
  codeText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#9ca3af",
  },
  title: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111111",
  },
  description: {
    fontSize: 12,
    color: "#6b7280",
    marginTop: 4,
    lineHeight: 16,
  },
  metricsRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 8,
    gap: 6,
  },
  metricItem: {
    fontSize: 11,
    color: "#6b7280",
  },
  metricVal: {
    fontWeight: "700",
    color: "#111111",
  },
  metricDot: {
    color: "#d1d5db",
    fontSize: 10,
  },
});
