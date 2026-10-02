import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { RegionalTrendContract } from "../types";

interface RegionalTrendCardProps {
  trend: RegionalTrendContract;
  onPressTrend?: (trendId: string) => void;
  testID?: string;
}

export const RegionalTrendCard: React.FC<RegionalTrendCardProps> = ({
  trend,
  onPressTrend,
  testID = `regional-trend-${trend.id}`,
}) => {
  const getMomentumColor = (m: string) => {
    switch (m) {
      case "surging":
        return "#dc2626";
      case "rising":
        return "#ea580c";
      default:
        return "#2563eb";
    }
  };

  return (
    <TouchableOpacity
      testID={testID}
      activeOpacity={0.85}
      onPress={() => onPressTrend?.(trend.id)}
      style={styles.card}
      accessibilityRole="button"
      accessibilityLabel={`Regional trend: ${trend.title} in ${trend.region_name}`}
    >
      <Image
        source={{ uri: trend.media_uri }}
        style={styles.image}
        resizeMode="cover"
      />

      <View style={styles.content}>
        <View style={styles.topRow}>
          <Text style={styles.regionName}>{trend.region_name.toUpperCase()}</Text>
          <View
            style={[
              styles.momentumBadge,
              { backgroundColor: getMomentumColor(trend.momentum) + "18" },
            ]}
          >
            <Text
              style={[
                styles.momentumText,
                { color: getMomentumColor(trend.momentum) },
              ]}
            >
              ● {trend.momentum.toUpperCase()}
            </Text>
          </View>
        </View>

        <Text style={styles.title}>{trend.title}</Text>
        <Text style={styles.narrative} numberOfLines={2}>
          {trend.context_narrative}
        </Text>

        <View style={styles.footer}>
          <Text style={styles.exploreLink}>Explore Trend Pieces →</Text>
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
  image: {
    width: "100%",
    height: 150,
    backgroundColor: "#f3f4f6",
  },
  content: {
    padding: 14,
  },
  topRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
  },
  regionName: {
    fontSize: 10,
    fontWeight: "700",
    color: "#6b7280",
    letterSpacing: 0.8,
  },
  momentumBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  momentumText: {
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  title: {
    fontSize: 16,
    fontWeight: "800",
    color: "#111111",
    lineHeight: 22,
  },
  narrative: {
    fontSize: 12,
    color: "#4b5563",
    marginTop: 4,
    lineHeight: 18,
  },
  footer: {
    marginTop: 10,
  },
  exploreLink: {
    fontSize: 12,
    fontWeight: "700",
    color: "#111111",
  },
});
