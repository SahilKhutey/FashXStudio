import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { RegionalHomeTemplateSpecContract } from "../types";
import { MapViewport } from "../components/MapViewport";
import { RegionCard } from "../components/RegionCard";
import { RegionalTrendCard } from "../components/RegionalTrendCard";

interface RegionalHomeTemplateProps {
  data: RegionalHomeTemplateSpecContract;
  onPressRegion?: (regionId: string) => void;
  onPressTrend?: (trendId: string) => void;
  onOpenExplorer?: () => void;
  onOpenMap?: () => void;
  testID?: string;
}

export const RegionalHomeTemplate: React.FC<RegionalHomeTemplateProps> = ({
  data,
  onPressRegion,
  onPressTrend,
  onOpenExplorer,
  onOpenMap,
  testID = "regional-home-screen",
}) => {
  return (
    <ScrollView
      testID={testID}
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}
    >
      {/* Hero Banner */}
      <View style={styles.heroBanner}>
        <View style={styles.heroTextArea}>
          <Text style={styles.heroTag}>GEOGRAPHIC FASHION</Text>
          <Text style={styles.heroTitle}>Explore Fashion by Place</Text>
          <Text style={styles.heroSubtitle}>
            Discover artisanal textiles, localized street styles, and weather-adapted wardrobes across global fashion capitals.
          </Text>
        </View>
        <TouchableOpacity
          testID="open-explorer-btn"
          style={styles.explorerCtaBtn}
          onPress={onOpenExplorer}
        >
          <Text style={styles.explorerCtaBtnText}>Browse Regions →</Text>
        </TouchableOpacity>
      </View>

      {/* Interactive Map Viewport Module */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionHeader}>INTERACTIVE FASHION MAP</Text>
          {onOpenMap && (
            <TouchableOpacity testID="open-fullscreen-map-btn" onPress={onOpenMap}>
              <Text style={styles.viewAllLink}>Fullscreen Map ↗</Text>
            </TouchableOpacity>
          )}
        </View>
        <MapViewport
          mapView={data.featured_map}
          onSelectMarker={onPressRegion}
        />
      </View>

      {/* Popular Fashion Regions Rail */}
      {data.popular_regions.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>POPULAR FASHION HUBS</Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.horizontalRail}
          >
            {data.popular_regions.map((reg) => (
              <RegionCard
                key={reg.id}
                region={reg}
                compact
                onPressRegion={onPressRegion}
              />
            ))}
          </ScrollView>
        </View>
      )}

      {/* Regional Trends Stream */}
      {data.regional_trends.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionHeader}>RISING REGIONAL TRENDS</Text>
          {data.regional_trends.map((trend) => (
            <RegionalTrendCard
              key={trend.id}
              trend={trend}
              onPressTrend={onPressTrend}
            />
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  content: {
    paddingBottom: 40,
  },
  heroBanner: {
    backgroundColor: "#111111",
    padding: 20,
    gap: 14,
  },
  heroTextArea: {
    gap: 4,
  },
  heroTag: {
    fontSize: 10,
    fontWeight: "800",
    color: "#9ca3af",
    letterSpacing: 1.5,
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: "800",
    color: "#ffffff",
  },
  heroSubtitle: {
    fontSize: 13,
    color: "#d1d5db",
    lineHeight: 18,
  },
  explorerCtaBtn: {
    backgroundColor: "#ffffff",
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignSelf: "flex-start",
  },
  explorerCtaBtnText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#111111",
  },
  section: {
    marginTop: 20,
    paddingHorizontal: 16,
  },
  sectionHeaderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: "800",
    color: "#6b7280",
    letterSpacing: 1,
  },
  viewAllLink: {
    fontSize: 11,
    fontWeight: "700",
    color: "#111111",
  },
  horizontalRail: {
    gap: 12,
  },
});
